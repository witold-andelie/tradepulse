import { createHash, randomUUID, timingSafeEqual } from "node:crypto";
import { readFileSync } from "node:fs";
import { appendFile, mkdir } from "node:fs/promises";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Ajv2020 } from "ajv/dist/2020.js";
import { fullFormats } from "ajv-formats/dist/formats.js";

import { HMEM } from "../vendor/hmem/reference/src/index.ts";
import { WorldModel } from "../vendor/world-model/reference/src/index.ts";

const MAX_BODY_BYTES = 5 * 1024 * 1024;
const MAX_ITEMS = 5000;
const MAX_RECALL = 100;
const MAX_STATE_RECORDS = 10000;
const MAX_WORLD_EVENTS = 100000;
const VERSION = "meterless-reference@1742dec";

type JsonObject = Record<string, unknown>;

// Compile the repository's actual contracts. There is no second, hand-maintained schema.
const apiSchema = JSON.parse(readFileSync(
  new URL("../../../contracts/api/tradepulse.schema.json", import.meta.url), "utf8",
));
const ajv = new Ajv2020({ strict: false });
for (const [name, format] of Object.entries(fullFormats)) ajv.addFormat(name, format);
const validators = Object.fromEntries(["GraphEdge", "ExtractedEvent"].map((name) => [
  name, ajv.compile({ $defs: apiSchema.$defs, $ref: `#/$defs/${name}` }),
]));

export type EngineServiceOptions = {
  dataDir: string;
  token?: string;
  clock?: () => Date;
};

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function asObject(value: unknown, label: string): JsonObject {
  if (!isObject(value)) throw new HttpError(400, `${label} must be an object`);
  return value;
}

function asString(value: unknown, label: string, maximum = 4096): string {
  if (typeof value !== "string" || value.length === 0 || value.length > maximum) {
    throw new HttpError(400, `${label} must be a non-empty string`);
  }
  return value;
}

function asDate(value: unknown, label: string): string {
  const date = asString(value, label, 10);
  const parsed = new Date(`${date}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(parsed.getTime()) ||
      parsed.toISOString().slice(0, 10) !== date) {
    throw new HttpError(400, `${label} must be an ISO date`);
  }
  return date;
}

function validateItems(items: JsonObject[], name: "GraphEdge" | "ExtractedEvent"): void {
  for (const item of items) {
    if (!validators[name](item)) throw new HttpError(400, `Invalid ${name} payload`);
    asString(item[name === "GraphEdge" ? "edge_id" : "event_id"], "identity", 128);
    if (name === "GraphEdge") {
      asString(item.src_symbol, "src_symbol", 32);
      asString(item.dst_symbol, "dst_symbol", 32);
    } else {
      asString(item.available_at, "available_at", 64);
    }
  }
}

function asItems(value: unknown, label: string): JsonObject[] {
  if (!Array.isArray(value) || value.length > MAX_ITEMS || value.some((item) => !isObject(item))) {
    throw new HttpError(400, `${label} must be a bounded list of objects`);
  }
  return value;
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (isObject(value)) {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function stanceText(tier: string): string {
  if (tier === "STRONG_OVERWEIGHT" || tier === "OVERWEIGHT") return "prefer exposure";
  if (tier === "UNDERWEIGHT" || tier === "AVOID") return "avoid exposure";
  if (tier === "NEUTRAL") return "keep neutral exposure";
  return "make no research call";
}

function secureEqual(left: string, right: string): boolean {
  const a = createHash("sha256").update(left).digest();
  const b = createHash("sha256").update(right).digest();
  return timingSafeEqual(a, b);
}

class HttpError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

async function readJson(request: IncomingMessage): Promise<JsonObject> {
  let size = 0;
  const chunks: Buffer[] = [];
  for await (const raw of request) {
    const chunk = Buffer.from(raw);
    size += chunk.length;
    if (size > MAX_BODY_BYTES) throw new HttpError(413, "request body is too large");
    chunks.push(chunk);
  }
  try {
    return asObject(JSON.parse(Buffer.concat(chunks).toString("utf8")), "request body");
  } catch (error) {
    if (error instanceof HttpError) throw error;
    throw new HttpError(400, "request body must be valid JSON");
  }
}

function send(response: ServerResponse, status: number, payload: unknown, requestId: string): void {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
    "x-request-id": requestId,
  });
  response.end(body);
}

function tradepulseRecord(memory: { content: string }): JsonObject | undefined {
  try {
    const decoded = JSON.parse(memory.content);
    return isObject(decoded) && isObject(decoded.tradepulseRecord)
      ? decoded.tradepulseRecord
      : undefined;
  } catch {
    return undefined;
  }
}

export class EngineService {
  readonly hmem: HMEM;
  readonly world: WorldModel;
  private mutationQueue: Promise<unknown> = Promise.resolve();
  private readonly activityPath: string;
  private readonly clock: () => Date;

  constructor(private readonly options: EngineServiceOptions) {
    this.clock = options.clock ?? (() => new Date());
    this.activityPath = path.join(options.dataDir, "activity.jsonl");
    this.hmem = new HMEM({
      actor: "tradepulse",
      persistDir: path.join(options.dataDir, "hmem"),
      clock: () => this.clock().getTime(),
    });
    this.world = new WorldModel({
      storage: "local",
      namespace: "tradepulse",
      directory: path.join(options.dataDir, "world-model"),
      clock: this.clock,
    });
  }

  private serial<T>(work: () => Promise<T> | T): Promise<T> {
    const result = this.mutationQueue.then(work);
    this.mutationQueue = result.catch(() => undefined);
    return result;
  }

  private authorized(request: IncomingMessage): boolean {
    if (!this.options.token) return true;
    const value = request.headers.authorization ?? "";
    const prefix = "Bearer ";
    return value.startsWith(prefix) && secureEqual(value.slice(prefix.length), this.options.token);
  }

  private async activity(requestId: string, operation: string, counts: JsonObject = {}): Promise<void> {
    await mkdir(this.options.dataDir, { recursive: true });
    const entry = {
      at: this.clock().toISOString(),
      request_id: requestId,
      component: "meterless-engines",
      operation,
      ...counts,
    };
    await appendFile(this.activityPath, `${JSON.stringify(entry)}\n`, "utf8");
    console.log(JSON.stringify(entry));
  }

  async handle(request: IncomingMessage, response: ServerResponse): Promise<void> {
    const requestId = randomUUID();
    try {
      const url = new URL(request.url ?? "/", "http://localhost");
      if (request.method === "GET" && url.pathname === "/health") {
        send(response, 200, {
          status: "ok",
          engines: { world_model: VERSION, hmem: VERSION },
        }, requestId);
        return;
      }
      if (!this.authorized(request)) throw new HttpError(401, "unauthorized");

      if (request.method === "POST" && url.pathname === "/world-model/events") {
        const events = asItems((await readJson(request)).events, "events");
        validateItems(events, "ExtractedEvent");
        const receipt = await this.serial(() => this.ingestEvents(events));
        await this.activity(requestId, "world-model.events", receipt);
        send(response, 200, receipt, requestId);
        return;
      }
      if (request.method === "POST" && url.pathname === "/world-model/edges") {
        const edges = asItems((await readJson(request)).edges, "edges");
        validateItems(edges, "GraphEdge");
        const receipt = await this.serial(() => this.upsertEdges(edges));
        await this.activity(requestId, "world-model.edges", receipt);
        send(response, 200, receipt, requestId);
        return;
      }
      if (request.method === "GET" && url.pathname === "/world-model/snapshot") {
        const asOf = asDate(url.searchParams.get("as_of"), "as_of");
        const snapshot = await this.serial(() => this.snapshot(asOf));
        await this.activity(requestId, "world-model.snapshot", {
          events: snapshot.events.length,
          edges: snapshot.edges.length,
        });
        send(response, 200, snapshot, requestId);
        return;
      }
      if (request.method === "POST" && url.pathname === "/hmem/records") {
        const records = asItems((await readJson(request)).records, "records");
        const receipt = await this.serial(() => this.remember(records));
        await this.activity(requestId, "hmem.records", receipt);
        send(response, 200, receipt, requestId);
        return;
      }
      if (request.method === "POST" && url.pathname === "/hmem/query") {
        const body = await readJson(request);
        const symbol = asString(body.symbol, "symbol", 32);
        const asOf = asDate(body.as_of, "as_of");
        const k = body.k;
        if (!Number.isInteger(k) || (k as number) < 1 || (k as number) > MAX_RECALL) {
          throw new HttpError(400, `k must be an integer from 1 to ${MAX_RECALL}`);
        }
        const records = await this.serial(() => this.recall(symbol, asOf, k as number));
        await this.activity(requestId, "hmem.query", { returned: records.length });
        send(response, 200, { records }, requestId);
        return;
      }
      if (request.method === "POST" && url.pathname === "/hmem/feedback") {
        const body = await readJson(request);
        const updated = await this.serial(() => this.feedback(body));
        await this.activity(requestId, "hmem.feedback", { updated });
        send(response, 200, { updated }, requestId);
        return;
      }
      if (request.method === "GET" && url.pathname === "/hmem/conflicts") {
        const symbol = asString(url.searchParams.get("symbol"), "symbol", 32);
        const conflicts = await this.serial(() => this.conflicts(symbol));
        await this.activity(requestId, "hmem.conflicts", { returned: conflicts.length });
        send(response, 200, { conflicts }, requestId);
        return;
      }
      if (request.method === "GET" && url.pathname === "/activity") {
        const ledger = this.hmem.ledger.all();
        send(response, 200, {
          hmem_records: this.hmem.store.all().length,
          hmem_ledger_entries: ledger.length,
          world_model_events: this.world.events().length,
          ledger_tail: ledger.slice(-20),
        }, requestId);
        return;
      }
      throw new HttpError(404, "not found");
    } catch (error) {
      const status = error instanceof HttpError ? error.status : 500;
      const message = error instanceof HttpError ? error.message : "internal server error";
      send(response, status, { error: message }, requestId);
    }
  }

  private knownWorldItems(kind: "tradepulseEvent" | "tradepulseEdge", key: string): Map<string, JsonObject> {
    const items = new Map<string, JsonObject>();
    for (const event of this.world.events()) {
      if (event.kind !== "upsertEntity") continue;
      const entity = event.payload as { attrs?: JsonObject };
      const value = entity.attrs?.[kind];
      if (isObject(value) && typeof value[key] === "string") items.set(value[key] as string, value);
    }
    return items;
  }

  private async ingestEvents(events: JsonObject[]): Promise<JsonObject> {
    const known = this.knownWorldItems("tradepulseEvent", "event_id");
    const proposed = new Map(known);
    for (const event of events) {
      const id = event.event_id as string;
      if (proposed.has(id) && canonical(proposed.get(id)) !== canonical(event)) {
        throw new HttpError(409, "Event identity already contains different data");
      }
      proposed.set(id, event);
    }
    if (this.world.events().length + events.length > MAX_WORLD_EVENTS) {
      throw new HttpError(413, "World Model event capacity reached");
    }
    let ingested = 0;
    let duplicates = 0;
    for (const event of events) {
      const id = asString(event.event_id, "event_id", 128);
      const at = asString(event.available_at, "available_at", 64);
      if (known.has(id)) {
        duplicates += 1;
        continue;
      }
      await this.world.upsertEntity({
        type: "tradepulse-event",
        externalKey: { system: "tradepulse", id },
        attrs: { tradepulseEvent: structuredClone(event) },
        source: { kind: "pipeline", by: "tradepulse", at },
      });
      known.set(id, event);
      ingested += 1;
    }
    return { ingested, duplicates };
  }

  private async upsertEdges(edges: JsonObject[]): Promise<JsonObject> {
    if (this.world.events().length + edges.length * 4 > MAX_WORLD_EVENTS) {
      throw new HttpError(413, "World Model event capacity reached");
    }
    const known = this.knownWorldItems("tradepulseEdge", "edge_id");
    for (const edge of edges) {
      const id = asString(edge.edge_id, "edge_id", 128);
      if (canonical(known.get(id)) === canonical(edge)) continue;
      const at = `${asDate(edge.valid_from, "valid_from")}T00:00:00.000Z`;
      const source = { kind: "pipeline", by: "tradepulse", at } as const;
      const src = asString(edge.src_symbol, "src_symbol", 32);
      const dst = asString(edge.dst_symbol, "dst_symbol", 32);
      const from = await this.world.upsertEntity({
        type: "instrument", externalKey: { system: "tradepulse", id: src },
        name: src, source,
      });
      const to = await this.world.upsertEntity({
        type: "instrument", externalKey: { system: "tradepulse", id: dst },
        name: dst, source,
      });
      await this.world.relate({
        from: from.id,
        to: to.id,
        type: asString(edge.relation, "relation", 64),
        context: `tradepulse-edge:${id}`,
        validFrom: at,
        attrs: { tradepulseEdge: structuredClone(edge) },
        source,
      });
      known.set(id, edge);
      await this.world.upsertEntity({
        type: "tradepulse-edge",
        externalKey: { system: "tradepulse", id },
        attrs: { tradepulseEdge: structuredClone(edge) },
        source,
      });
    }
    return { upserted: edges.length };
  }

  private snapshot(asOf: string): { as_of: string; events: JsonObject[]; edges: JsonObject[] } {
    const eventMap = new Map<string, JsonObject>();
    const edgeMap = new Map<string, JsonObject>();
    const edgeTimes = new Map<string, string>();
    const cutoff = Date.parse(`${asOf}T23:59:59.999Z`);
    for (const event of this.world.events()) {
      if (event.kind !== "upsertEntity") continue;
      const entity = event.payload as { attrs?: JsonObject };
      const marketEvent = entity.attrs?.tradepulseEvent;
      const edge = entity.attrs?.tradepulseEdge;
      if (isObject(marketEvent) && typeof marketEvent.event_id === "string" &&
          typeof marketEvent.available_at === "string" &&
          Date.parse(marketEvent.available_at) <= cutoff) {
        eventMap.set(marketEvent.event_id, marketEvent);
      }
      if (isObject(edge) && typeof edge.edge_id === "string" &&
          typeof edge.valid_from === "string" && edge.valid_from <= asOf &&
          edge.valid_from >= (edgeTimes.get(edge.edge_id) ?? "")) {
        edgeMap.set(edge.edge_id, edge);
        edgeTimes.set(edge.edge_id, edge.valid_from);
      }
    }
    const events = [...eventMap.values()].filter((item) =>
      typeof item.available_at === "string" && Date.parse(item.available_at) <= cutoff
    );
    const edges = [...edgeMap.values()].filter((item) =>
      typeof item.valid_from === "string" && item.valid_from <= asOf
    );
    if (events.length > MAX_ITEMS || edges.length > MAX_ITEMS) {
      throw new HttpError(413, "Snapshot exceeds the agreed item limit");
    }
    return { as_of: asOf, events, edges };
  }

  private remember(records: JsonObject[]): JsonObject {
    const known = new Map(this.hmem.store.all().flatMap((memory) => {
      const record = tradepulseRecord(memory);
      return record && typeof record.id === "string" ? [[record.id, record] as const] : [];
    }));
    const proposed = new Map(known);
    for (const record of records) {
      this.validateRecord(record);
      const id = record.id as string;
      if (proposed.has(id) && canonical(proposed.get(id)) !== canonical(record)) {
        throw new HttpError(409, "Memory identity already contains different data");
      }
      proposed.set(id, record);
    }
    if (proposed.size > MAX_STATE_RECORDS) throw new HttpError(413, "H-MEM capacity reached");
    let added = 0;
    for (const record of records) {
      const id = asString(record.id, "id", 128);
      const symbol = asString(record.symbol, "symbol", 32);
      const asOf = asDate(record.as_of, "as_of");
      const tier = asString(record.tier, "tier", 32);
      const provenance = asObject(record.provenance, "provenance");
      const runId = asString(provenance.run_id, "provenance.run_id", 128);
      if (known.has(id)) continue;
      const payload = {
        version: 1,
        summary: `TradePulse research stance for ${symbol}: ${stanceText(tier)} as of ${asOf}.`,
        tradepulseRecord: structuredClone(record),
      };
      this.hmem.add({
        content: JSON.stringify(payload),
        type: "factual",
        layer: "long_term",
        tags: [
          "project:tradepulse",
          `symbol:${symbol}`,
          `as-of:${asOf}`,
          `tier:${tier}`,
          `tradepulse-record:${id}`,
        ],
        source: `tradepulse:${runId}`,
        provenance: {
          origin: "plan_completion",
          learnedAt: this.clock().getTime(),
          label: `TradePulse run ${runId}`,
          refs: Array.isArray(provenance.evidence_ids)
            ? provenance.evidence_ids.filter((value): value is string => typeof value === "string")
            : [],
        },
      });
      known.set(id, record);
      added += 1;
    }
    return { added };
  }

  private recall(symbol: string, asOf: string, k: number): JsonObject[] {
    // The core consumes dated counts only. Keep future feedback and access history out of
    // historical selection. Use the official H-MEM store and audit services without touching
    // ineligible records or ranking them against future memories.
    const eligible = this.hmem.store.all().flatMap((memory) => {
      const record = tradepulseRecord(memory);
      return record && record.symbol === symbol &&
        typeof record.as_of === "string" && record.as_of <= asOf
        ? [{ memory, record }] : [];
    });
    eligible.sort((a, b) => String(b.record.as_of).localeCompare(String(a.record.as_of)) ||
      String(a.record.id).localeCompare(String(b.record.id)));
    const selected = eligible.slice(0, k);
    for (const { memory } of selected) {
      this.hmem.store.touch(memory.id);
      this.hmem.ledger.log(memory.id, "read", "tradepulse", {
        details: { symbol, as_of: asOf, strategy: "dated-research-records" },
      });
    }
    this.hmem.store.persist();
    return selected.map(({ record }) => structuredClone(record));
  }

  private validateRecord(record: JsonObject): void {
    asString(record.id, "id", 128);
    asString(record.symbol, "symbol", 32);
    asDate(record.as_of, "as_of");
    const tier = asString(record.tier, "tier", 32);
    if (!["STRONG_OVERWEIGHT", "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT", "AVOID", "NO_CALL"].includes(tier)) {
      throw new HttpError(400, "Invalid research tier");
    }
    if (!Number.isInteger(record.horizon_days) || (record.horizon_days as number) < 1 ||
        (record.horizon_days as number) > 252) throw new HttpError(400, "Invalid memory horizon");
    asObject(record.content, "content");
    const provenance = asObject(record.provenance, "provenance");
    asString(provenance.run_id, "run_id", 128);
    if (!Array.isArray(provenance.evidence_ids) || provenance.evidence_ids.length > 1000 ||
        provenance.evidence_ids.some((id) => typeof id !== "string")) {
      throw new HttpError(400, "Invalid evidence identifiers");
    }
  }

  private feedback(body: JsonObject): number {
    const id = asString(body.id, "id", 128);
    const outcome = asObject(body.outcome, "outcome");
    if (typeof outcome.hit !== "boolean" || typeof outcome.excess_return !== "number" ||
        !Number.isFinite(outcome.excess_return)) {
      throw new HttpError(400, "outcome requires finite excess_return and boolean hit");
    }
    const memory = this.hmem.store.all().find((item) =>
      item.tags.includes(`tradepulse-record:${id}`)
    );
    if (!memory) throw new HttpError(404, "memory record not found");
    const priorFeedback = this.hmem.ledger.history(memory.id).find((entry) =>
      entry.action === "feedback" && isObject(entry.details?.tradepulseOutcome)
    );
    if (priorFeedback) {
      if (canonical(priorFeedback.details?.tradepulseOutcome) !== canonical(outcome)) {
        throw new HttpError(409, "Memory record already has different settled feedback");
      }
      return 1;
    }
    this.hmem.feedback(memory.id, outcome.hit ? "helpful" : "wrong");
    this.hmem.ledger.log(memory.id, "feedback", "tradepulse-settlement", {
      details: { tradepulseOutcome: structuredClone(outcome) },
    });
    this.hmem.store.update(memory.id, {
      tags: [...new Set([...memory.tags, `settled:${outcome.hit ? "hit" : "miss"}`])],
    });
    return 1;
  }

  private conflicts(symbol: string): JsonObject[] {
    // Isolate scanning to the symbol and cap quadratic work. Official conflict detection is
    // unchanged; this temporary engine has no persistence and never auto-resolves records.
    const scoped = new HMEM({ clock: () => this.clock().getTime() });
    const matches = this.hmem.store.all().filter((memory) =>
      tradepulseRecord(memory)?.symbol === symbol
    ).sort((a, b) => String(tradepulseRecord(b)?.as_of).localeCompare(
      String(tradepulseRecord(a)?.as_of),
    ));
    if (matches.length > 250) throw new HttpError(413, "Conflict scan exceeds 250 symbol records");
    scoped.store.restoreAll(matches, matches.length);
    const found = scoped.conflicts.scan();
    const byId = new Map(this.hmem.store.all().map((memory) => [memory.id, memory]));
    return found.flatMap((conflict) => {
      const left = byId.get(conflict.memoryA);
      const right = byId.get(conflict.memoryB);
      if (!left || !right) return [];
      const a = tradepulseRecord(left);
      const b = tradepulseRecord(right);
      if (!a || !b || a.symbol !== symbol || b.symbol !== symbol) return [];
      const direction = (tier: unknown) => tier === "OVERWEIGHT" || tier === "STRONG_OVERWEIGHT"
        ? 1 : tier === "UNDERWEIGHT" || tier === "AVOID" ? -1 : 0;
      if (direction(a.tier) * direction(b.tier) !== -1 || a.horizon_days !== b.horizon_days) return [];
      const pair = [String(a.id), String(b.id)].sort().join(":");
      if (!this.hmem.ledger.all().some((entry) => entry.action === "conflict_detected" &&
          entry.details?.tradepulsePair === pair)) {
        this.hmem.ledger.log(left.id, "conflict_detected", "tradepulse", {
          details: { tradepulsePair: pair, reason: conflict.reason, confidence: conflict.confidence },
        });
      }
      return [{
        id: createHash("sha256").update(pair).digest("hex"),
        record_a: a.id,
        record_b: b.id,
        as_of_a: a.as_of,
        as_of_b: b.as_of,
        reason: conflict.reason,
        confidence: conflict.confidence,
        resolved: conflict.resolved,
      }];
    });
  }
}

export function createAppServer(options: EngineServiceOptions) {
  const service = new EngineService(options);
  const server = createServer((request, response) => service.handle(request, response));
  server.requestTimeout = 30000;
  server.headersTimeout = 15000;
  return { service, server };
}

async function main(): Promise<void> {
  const port = Number(process.env.ENGINES_PORT ?? "8790");
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error("invalid ENGINES_PORT");
  const dataDir = path.resolve(process.env.ENGINES_DATA_DIR ?? "runs/engines");
  const host = process.env.ENGINES_HOST ?? "127.0.0.1";
  const { server } = createAppServer({ dataDir, token: process.env.ENGINES_TOKEN });
  server.listen(port, host, () => console.log(JSON.stringify({
    component: "meterless-engines",
    status: "listening",
    host,
    port,
  })));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : "failed to start");
    process.exitCode = 1;
  });
}
