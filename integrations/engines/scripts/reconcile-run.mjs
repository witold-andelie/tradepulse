// Read-only reconciliation of stored records; never upgrades a failed pipeline report.
import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import { pathToFileURL } from "node:url";

export function reconcile(records, runId, expectedCount) {
  if (!/^[a-z0-9-]{8,64}$/.test(runId) || !Number.isInteger(expectedCount) ||
      expectedCount < 1 || expectedCount > 5000 || !Array.isArray(records) || records.length > 10000) {
    throw new Error("Invalid reconciliation bounds");
  }
  const ids = new Set(), symbols = new Set(), pools = new Set(), dates = new Set();
  let found = 0, invalid = 0;
  for (const memory of records) {
    if (memory.source !== `tradepulse:${runId}`) continue;
    found++;
    let record;
    try { record = JSON.parse(memory.content).tradepulseRecord; }
    catch { invalid++; continue; }
    const row = record?.content?.recommendation;
    const identity = [runId, record?.content?.pool, record?.symbol, record?.as_of, record?.horizon_days];
    // EngineBridge hashes Python json.dumps(list), including its default comma spaces.
    const externalId = createHash("sha256").update(`[${identity.map(x => JSON.stringify(x)).join(", ")}]`).digest("hex");
    if (!record || record.provenance?.run_id !== runId || record.id !== externalId ||
        ids.has(record.id) || row?.symbol !== record.symbol || row?.pool !== record.content.pool ||
        row?.horizon_days !== record.horizon_days || row?.tier !== record.tier) invalid++;
    ids.add(record?.id); symbols.add(record?.symbol); pools.add(record?.content?.pool); dates.add(record?.as_of);
  }
  const matched = found === expectedCount && ids.size === expectedCount && invalid === 0;
  return { status: matched ? "persistence-reconciled" : "persistence-mismatch", read_only: true,
    run_acceptance_passed: false, run_id: runId, expected_count: expectedCount,
    stored_records: found, unique_record_ids: ids.size, unique_symbols: symbols.size,
    invalid_records: invalid, pools: [...pools], decision_dates: [...dates] };
}

if (process.argv[1] === "-" || (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)) {
  try {
    const args = process.argv.slice(2);
    if (args.length !== 6) throw new Error("Use --state PATH --run-id ID --expected-count N");
    const options = Object.fromEntries([0, 2, 4].map(i => [args[i], args[i + 1]]));
    const filename = options["--state"];
    if (statSync(filename).size > 128 * 1024 * 1024) throw new Error("State exceeds the work limit");
    const raw = readFileSync(filename);
    const result = reconcile(JSON.parse(raw).records, options["--run-id"], Number(options["--expected-count"]));
    result.state_sha256 = createHash("sha256").update(raw).digest("hex");
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.status === "persistence-reconciled" ? 0 : 1;
  } catch {
    console.error("Reconciliation failed; inspect arguments and state locally without printing private content.");
    process.exitCode = 1;
  }
}
