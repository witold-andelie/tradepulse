import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { createAppServer, EngineService } from "../src/server.ts";

const EVENT = {
  event_id: "event-1",
  doc_sha256: "a".repeat(64),
  accession_number: "accession-1",
  symbol: "NVDA",
  event_type: "customer_win",
  available_at: "2026-10-20T20:05:00Z",
  direction: 1,
  novelty: "new",
  counterparty: null,
  counterparty_symbol: null,
  magnitude_usd: null,
  demand_signals: [],
  quote: "customer win",
  extractor_model: "meterless/auto",
  schema_version: "1.0",
};

const EDGE = {
  edge_id: "edge-1",
  src_symbol: "NVDA",
  dst_symbol: "TSM",
  relation: "supplier_of",
  weight: 0.6,
  source: "seed",
  evidence_ref: null,
  status: "validated",
  lead_lag_t: 2.4,
  valid_from: "2026-10-20",
};

function record(id: string, tier: string, asOf: string) {
  return {
    id,
    symbol: "NVDA",
    as_of: asOf,
    tier,
    horizon_days: 5,
    content: { pool: "us_equity", recommendation: { symbol: "NVDA", tier } },
    provenance: { run_id: `run-${id}`, evidence_ids: ["evidence-1"] },
  };
}

describe("Meterless engines sidecar", () => {
  const cleanups: (() => Promise<void>)[] = [];

  afterEach(async () => {
    while (cleanups.length) await cleanups.pop()!();
  });

  async function start(token?: string) {
    const dataDir = await mkdtemp(path.join(tmpdir(), "tradepulse-engines-"));
    const app = createAppServer({
      dataDir,
      token,
      clock: () => new Date("2026-10-27T12:00:00Z"),
    });
    await new Promise<void>((resolve) => app.server.listen(0, "127.0.0.1", resolve));
    const address = app.server.address();
    if (!address || typeof address === "string") throw new Error("missing test port");
    const base = `http://127.0.0.1:${address.port}`;
    cleanups.push(async () => {
      await new Promise<void>((resolve, reject) => app.server.close((error) =>
        error ? reject(error) : resolve()
      ));
      await rm(dataDir, { recursive: true, force: true });
    });
    return { ...app, base, dataDir };
  }

  async function json(base: string, route: string, init?: RequestInit) {
    const response = await fetch(`${base}${route}`, init);
    return { response, body: await response.json() as Record<string, unknown> };
  }

  it("runs World Model ingestion, idempotency and as-of snapshots", async () => {
    const { base } = await start();
    const health = await json(base, "/health");
    expect(health.response.status).toBe(200);
    expect(health.body.status).toBe("ok");

    const first = await json(base, "/world-model/events", {
      method: "POST", body: JSON.stringify({ events: [EVENT] }),
    });
    const second = await json(base, "/world-model/events", {
      method: "POST", body: JSON.stringify({ events: [EVENT] }),
    });
    expect(first.body).toMatchObject({ ingested: 1, duplicates: 0 });
    expect(second.body).toMatchObject({ ingested: 0, duplicates: 1 });

    const edges = await json(base, "/world-model/edges", {
      method: "POST", body: JSON.stringify({ edges: [EDGE] }),
    });
    expect(edges.body).toMatchObject({ upserted: 1 });
    const before = await json(base, "/world-model/snapshot?as_of=2026-10-19");
    expect(before.body).toMatchObject({ events: [], edges: [] });
    const after = await json(base, "/world-model/snapshot?as_of=2026-10-20");
    expect(after.body).toMatchObject({ as_of: "2026-10-20", events: [EVENT], edges: [EDGE] });
  });

  it("uses H-MEM for recall, feedback, conflicts and an auditable activity view", async () => {
    const { base } = await start();
    const records = [
      record("rec-1", "OVERWEIGHT", "2026-10-20"),
      record("rec-2", "AVOID", "2026-10-21"),
    ];
    const saved = await json(base, "/hmem/records", {
      method: "POST", body: JSON.stringify({ records }),
    });
    expect(saved.body).toMatchObject({ added: 2 });

    const recall = await json(base, "/hmem/query", {
      method: "POST",
      body: JSON.stringify({ symbol: "NVDA", as_of: "2026-10-20", k: 10 }),
    });
    expect(recall.body.records).toEqual([records[0]]);

    const settled = await json(base, "/hmem/feedback", {
      method: "POST",
      body: JSON.stringify({ id: "rec-1", outcome: { excess_return: 0.02, hit: true } }),
    });
    expect(settled.body).toMatchObject({ updated: 1 });

    const conflicts = await json(base, "/hmem/conflicts?symbol=NVDA");
    expect(Array.isArray(conflicts.body.conflicts)).toBe(true);
    expect((conflicts.body.conflicts as unknown[]).length).toBeGreaterThan(0);

    const activity = await json(base, "/activity");
    expect(activity.body).toMatchObject({ hmem_records: 2 });
    expect(activity.body.hmem_ledger_entries).toEqual(expect.any(Number));
    expect((activity.body.hmem_ledger_entries as number)).toBeGreaterThanOrEqual(5);
  });

  it("protects non-health routes when a token is configured", async () => {
    const { base } = await start("test-token");
    expect((await json(base, "/health")).response.status).toBe(200);
    expect((await json(base, "/activity")).response.status).toBe(401);
    const allowed = await json(base, "/activity", {
      headers: { authorization: "Bearer test-token" },
    });
    expect(allowed.response.status).toBe(200);
  });

  it("keeps earlier edge versions in historical snapshots after later or out-of-order writes", async () => {
    const { base } = await start();
    const versions = [EDGE, { ...EDGE, valid_from: "2026-10-25", weight: 0.2 },
      { ...EDGE, valid_from: "2026-10-23", weight: 0.4 }];
    for (const edge of versions) {
      expect((await json(base, "/world-model/edges", {
        method: "POST", body: JSON.stringify({ edges: [edge] }),
      })).response.status).toBe(200);
    }
    const early = await json(base, "/world-model/snapshot?as_of=2026-10-21");
    expect(early.body.edges).toEqual([EDGE]);
    const late = await json(base, "/world-model/snapshot?as_of=2026-10-26");
    expect(late.body.edges).toEqual([versions[1]]);
  });

  it("rejects invalid contract batches before writing any event", async () => {
    const { base, service } = await start();
    const invalid = await json(base, "/world-model/events", {
      method: "POST", body: JSON.stringify({ events: [EVENT, { ...EVENT, direction: 42 }] }),
    });
    expect(invalid.response.status).toBe(400);
    expect(service.world.events()).toHaveLength(0);
    expect((await json(base, "/world-model/snapshot?as_of=2026-02-30")).response.status).toBe(400);
  });

  it("rejects changed immutable event and memory identities", async () => {
    const { base } = await start();
    await json(base, "/world-model/events", {
      method: "POST", body: JSON.stringify({ events: [EVENT] }),
    });
    const changed = await json(base, "/world-model/events", {
      method: "POST", body: JSON.stringify({ events: [{ ...EVENT, direction: -1 }] }),
    });
    expect(changed.response.status).toBe(409);
    const rec = record("rec-stable", "OVERWEIGHT", "2026-10-20");
    for (const [value, expected] of [[rec, 200], [{ ...rec, tier: "AVOID" }, 409]] as const) {
      expect((await json(base, "/hmem/records", {
        method: "POST", body: JSON.stringify({ records: [value] }),
      })).response.status).toBe(expected);
    }
  });

  it("does not read or touch future or different-symbol memories", async () => {
    const { base, service } = await start();
    const records = [record("old", "OVERWEIGHT", "2026-10-20"),
      record("future", "AVOID", "2026-10-25"),
      { ...record("other", "NEUTRAL", "2026-10-20"), symbol: "TSM" }];
    await json(base, "/hmem/records", { method: "POST", body: JSON.stringify({ records }) });
    await json(base, "/hmem/query", {
      method: "POST", body: JSON.stringify({ symbol: "NVDA", as_of: "2026-10-21", k: 10 }),
    });
    const all = service.hmem.store.all();
    expect(all.map((item) => item.accessCount)).toEqual([1, 0, 0]);
    expect(service.hmem.ledger.all().filter((entry) => entry.action === "read")).toHaveLength(1);
  });

  it("persists memory, world history and idempotent settlement across restarts", async () => {
    const { base, dataDir, service } = await start();
    await json(base, "/world-model/events", {
      method: "POST", body: JSON.stringify({ events: [EVENT] }),
    });
    const rec = record("persisted", "OVERWEIGHT", "2026-10-20");
    await json(base, "/hmem/records", { method: "POST", body: JSON.stringify({ records: [rec] }) });
    const feedback = { id: rec.id, outcome: { excess_return: 0.02, hit: true } };
    await json(base, "/hmem/feedback", { method: "POST", body: JSON.stringify(feedback) });
    const confidence = service.hmem.store.all()[0].confidence;
    await json(base, "/hmem/feedback", { method: "POST", body: JSON.stringify(feedback) });
    expect(service.hmem.store.all()[0].confidence).toBe(confidence);
    expect((await json(base, "/hmem/feedback", {
      method: "POST", body: JSON.stringify({ ...feedback, outcome: { excess_return: -0.1, hit: false } }),
    })).response.status).toBe(409);
    const restored = new EngineService({ dataDir });
    expect(restored.hmem.store.all()).toHaveLength(1);
    expect(restored.hmem.store.all()[0].confidence).toBe(confidence);
    expect(restored.world.events().length).toBeGreaterThan(0);
    expect(restored.hmem.ledger.all().some((entry) => entry.details?.tradepulseOutcome)).toBe(true);
  });
});
