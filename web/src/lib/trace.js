// Pair only recorded node boundaries. Retain incomplete events for inspection.
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
    if (event.kind === 'node_end') {
      const start = pending.get(event.node)?.shift();
      if (!start) { unmatchedEnds += 1; continue; }
      pairs.push({ start, end: event, intervalMs: Date.parse(event.ts) - Date.parse(start.ts), reportedMs: event.duration_ms });
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
