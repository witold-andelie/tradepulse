// Pure data helpers for the pages (task B1). They never mutate their inputs.

/**
 * Filter recommendations.
 * opts.pool: exact match when set.
 * opts.query: case-insensitive substring of symbol OR name when non-empty (trimmed).
 * opts.sector: exact match when set.
 * opts.tiers: array of tiers to keep when non-empty.
 */
export function filterRecommendations(rows, opts = {}) {
  const query = (opts.query || '').trim().toLowerCase();
  return rows.filter((row) => (
    (!opts.pool || row.pool === opts.pool)
    && (!query || row.symbol.toLowerCase().includes(query) || row.name.toLowerCase().includes(query))
    && (!opts.sector || row.sector === opts.sector)
    && (!opts.tiers?.length || opts.tiers.includes(row.tier))
  ));
}

/**
 * Return a NEW array sorted by `key` ("rank", "score", "net_edge_bps", "symbol", ...).
 * dir: "asc" (default) or "desc". null/undefined values always go last, whatever the direction.
 */
export function sortRecommendations(rows, key = 'rank', dir = 'asc') {
  return [...rows].sort((a, b) => {
    const left = a[key];
    const right = b[key];
    if (left == null && right == null) return 0;
    if (left == null) return 1;
    if (right == null) return -1;
    const order = left < right ? -1 : left > right ? 1 : 0;
    return dir === 'desc' ? -order : order;
  });
}

/**
 * One entry per sector: { sector, count, meanScore, overweight, underweight }.
 * overweight counts STRONG_OVERWEIGHT + OVERWEIGHT; underweight counts UNDERWEIGHT + AVOID.
 * Sorted by meanScore descending.
 */
export function sectorSummary(rows) {
  const sectors = new Map();
  for (const row of rows) {
    const entry = sectors.get(row.sector) || {
      sector: row.sector, count: 0, meanScore: 0, overweight: 0, underweight: 0,
    };
    entry.count += 1;
    entry.meanScore += row.score;
    if (['STRONG_OVERWEIGHT', 'OVERWEIGHT'].includes(row.tier)) entry.overweight += 1;
    if (['UNDERWEIGHT', 'AVOID'].includes(row.tier)) entry.underweight += 1;
    sectors.set(row.sector, entry);
  }
  return [...sectors.values()]
    .map((entry) => ({ ...entry, meanScore: entry.meanScore / entry.count }))
    .sort((a, b) => b.meanScore - a.meanScore);
}

/** A recommendation's contributions sorted by absolute contribution, largest first (new array). */
export function contributionsSorted(rec) {
  return [...rec.contributions].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
}

/**
 * Banner for the run's data_mode:
 * SYNTHETIC -> { show: true, tone: "warning", text: "SYNTHETIC FIXTURE — fictional instruments, generated numbers. Not results." }
 * REPLAY    -> { show: true, tone: "info", text: "REPLAY — sample data with recorded model answers." }
 * REAL      -> { show: false, tone: "none", text: "" }
 * Anything else throws.
 */
export function dataModeBanner(dataMode) {
  switch (dataMode) {
    case 'SYNTHETIC':
      return { show: true, tone: 'warning', text: 'SYNTHETIC FIXTURE — fictional instruments, generated numbers. Not results.' };
    case 'REPLAY':
      return { show: true, tone: 'info', text: 'REPLAY — sample data with recorded model answers.' };
    case 'REAL':
      return { show: false, tone: 'none', text: '' };
    default:
      throw new Error('Unknown data mode');
  }
}
