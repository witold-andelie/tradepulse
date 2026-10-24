// Pair only recorded node boundaries. Retain incomplete events for inspection.
// A span that raises ends with an `error` event carrying duration_ms instead of `node_end`
// (tradepulse/trace.py Tracer.span), so such an event also closes the open start.
const closesSpan = (event) => event.kind === 'node_end' || (event.kind === 'error' && event.duration_ms != null);

export function summarizeTrace(events) {
  const ordered = [...events].sort((a, b) => a.seq - b.seq);
  const pending = new Map();
  const pairs = [];
  let unmatchedEnds = 0;
  for (const event of ordered) {
    if (event.kind === 'node_start') {
      if (!pending.has(event.node)) pending.set(event.node, []);
      pending.get(event.node).push(event);
    }
    if (closesSpan(event)) {
      const start = pending.get(event.node)?.shift();
      if (!start) { if (event.kind === 'node_end') unmatchedEnds += 1; continue; }
      pairs.push({ start, end: event, failed: event.kind === 'error', intervalMs: Date.parse(event.ts) - Date.parse(start.ts), reportedMs: event.duration_ms });
    }
  }
  const timestamps = ordered.map((event) => Date.parse(event.ts));
  const firstMs = timestamps.length ? Math.min(...timestamps) : null;
  const lastMs = timestamps.length ? Math.max(...timestamps) : null;
  return {
    ordered, pairs, unmatchedEnds,
    unmatchedStarts: [...pending.values()].reduce((sum, values) => sum + values.length, 0),
    firstMs, spanMs: events.length ? lastMs - firstMs : null,
    llmCalls: events.filter((event) => event.kind === 'llm_call').length,
    tokensIn: events.reduce((sum, event) => sum + (event.tokens_in ?? 0), 0),
    tokensOut: events.reduce((sum, event) => sum + (event.tokens_out ?? 0), 0),
    tokenReports: events.filter((event) => event.tokens_in != null || event.tokens_out != null).length,
  };
}

// Reported durations come from a monotonic clock truncated to whole milliseconds, while event
// timestamps come from the wall clock, so the two differ slightly on every real span. Only a
// difference above both tolerances counts as a discrepancy.
export const TIMING_TOLERANCE_MS = 5;
export const TIMING_TOLERANCE_SHARE = 0.01;

export function timingDiffers(pair) {
  if (pair.reportedMs == null || !Number.isFinite(pair.intervalMs)) return false;
  const difference = Math.abs(pair.reportedMs - pair.intervalMs);
  return difference > TIMING_TOLERANCE_MS
    && difference > TIMING_TOLERANCE_SHARE * Math.max(Math.abs(pair.reportedMs), Math.abs(pair.intervalMs));
}
