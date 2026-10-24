import { describe, expect, it } from 'vitest';
import { summarizeTrace, timingDiffers } from './trace.js';

const base = { tokens_in: null, tokens_out: null, model: null, status: 'ok', duration_ms: null };
const start = { ...base, seq: 0, ts: '2026-10-22T08:00:00Z', node: 'rank:us_equity', kind: 'node_start' };

describe('trace pairing against the backend tracer', () => {
  it('closes a span that raised with its error event', () => {
    const failed = { ...base, seq: 1, ts: '2026-10-22T08:00:01.250Z', node: 'rank:us_equity', kind: 'error', status: 'error', duration_ms: 1249 };
    const result = summarizeTrace([start, failed]);
    expect(result.pairs).toHaveLength(1);
    expect(result.pairs[0].failed).toBe(true);
    expect(result.pairs[0].end.status).toBe('error');
    expect(result.unmatchedStarts).toBe(0);
  });

  it('does not treat an item-level error without duration as a span end', () => {
    const itemError = { ...base, seq: 1, ts: '2026-10-22T08:00:00.500Z', node: 'rank:us_equity', kind: 'error', status: 'error' };
    const end = { ...base, seq: 2, ts: '2026-10-22T08:00:01Z', node: 'rank:us_equity', kind: 'node_end', duration_ms: 1000 };
    const result = summarizeTrace([start, itemError, end]);
    expect(result.pairs).toHaveLength(1);
    expect(result.pairs[0].end.seq).toBe(2);
    expect(result.pairs[0].failed).toBe(false);
    expect(result.unmatchedEnds).toBe(0);
  });

  it('keeps an unrelated error out of the unmatched-end count', () => {
    const lonely = { ...base, seq: 0, ts: '2026-10-22T08:00:00Z', node: 'explain:SYN001', kind: 'error', status: 'error' };
    expect(summarizeTrace([lonely]).unmatchedEnds).toBe(0);
  });
});

describe('timing discrepancy tolerance', () => {
  it('ignores clock jitter and millisecond truncation', () => {
    expect(timingDiffers({ reportedMs: 3861, intervalMs: 3862 })).toBe(false);
    expect(timingDiffers({ reportedMs: 0, intervalMs: 4 })).toBe(false);
  });

  it('flags a real disagreement', () => {
    expect(timingDiffers({ reportedMs: 407, intervalMs: 5 })).toBe(true);
    expect(timingDiffers({ reportedMs: 10000, intervalMs: 10200 })).toBe(true);
  });

  it('needs both tolerances to be exceeded', () => {
    expect(timingDiffers({ reportedMs: 100000, intervalMs: 100500 })).toBe(false); // 0.5 %
    expect(timingDiffers({ reportedMs: 100, intervalMs: 104 })).toBe(false); // 4 ms
  });

  it('cannot differ without a reported duration', () => {
    expect(timingDiffers({ reportedMs: null, intervalMs: 50 })).toBe(false);
  });
});
