import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { reconcile } from "./reconcile-run.mjs";

// SYNTHETIC persistence objects, not captured runtime evidence.
function fixture() {
  const run = "synthetic-run-123";
  const identity = [run, "us_equity", "SYNTHETIC", "2026-10-23", 5];
  const record = { id: createHash("sha256").update(`[${identity.map(x => JSON.stringify(x)).join(", ")}]`).digest("hex"),
    symbol: "SYNTHETIC", as_of: "2026-10-23", horizon_days: 5, tier: "NO_CALL",
    content: { pool: "us_equity", recommendation: { symbol: "SYNTHETIC", pool: "us_equity",
      horizon_days: 5, tier: "NO_CALL" } }, provenance: { run_id: run } };
  return { run, memory: { source: `tradepulse:${run}`, content: JSON.stringify({ tradepulseRecord: record }) } };
}

test("reconciliation is read-only and never declares pipeline acceptance", () => {
  const { run, memory } = fixture();
  const original = JSON.stringify(memory);
  const result = reconcile([memory], run, 1);
  assert.equal(result.status, "persistence-reconciled");
  assert.equal(result.run_acceptance_passed, false);
  assert.equal(JSON.stringify(memory), original);
});

test("duplicates or missing records fail reconciliation", () => {
  const { run, memory } = fixture();
  assert.equal(reconcile([memory, memory], run, 2).status, "persistence-mismatch");
  assert.equal(reconcile([], run, 1).status, "persistence-mismatch");
});
