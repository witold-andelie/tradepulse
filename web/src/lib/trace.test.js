import { describe, expect, it } from 'vitest';
import { summarizeTrace } from './trace.js';
const start = { seq: 0, ts: '2026-10-22T08:00:00Z', node: 'verify', kind: 'node_start', duration_ms: null, tokens_in: null, tokens_out: null };
const end = { ...start, seq: 1, ts: '2026-10-22T08:00:00.005Z', kind: 'node_end', duration_ms: 2000, tokens_in: 10, tokens_out: 2 };
describe('trace accounting', () => {
  it('keeps timestamp interval separate from reported duration and does not infer LLM calls', () => {
    const result = summarizeTrace([end, start]);
    expect(result.pairs[0].intervalMs).toBe(5);
    expect(result.pairs[0].reportedMs).toBe(2000);
    expect(result.spanMs).toBe(5);
    expect(result.llmCalls).toBe(0);
    expect(result.tokensIn).toBe(10);
    expect(result.tokensOut).toBe(2);
  });
  it('retains unmatched boundaries and pairs repeated node occurrences', () => {
    const result = summarizeTrace([start, end, { ...start, seq: 2 }, { ...end, seq: 3 }, { ...start, node: 'open', seq: 4 }, { ...end, node: 'orphan', seq: 5 }]);
    expect(result.pairs).toHaveLength(2);
    expect(result.unmatchedStarts).toBe(1);
    expect(result.unmatchedEnds).toBe(1);
  });
  it('does not fabricate an elapsed duration for an empty trace', () => {
    expect(summarizeTrace([]).spanMs).toBeNull();
  });
});
