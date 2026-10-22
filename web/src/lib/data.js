// Pure data helpers for the pages (task B1). They never mutate their inputs.

/**
 * Filter recommendations.
 * opts.pool: exact match when set.
 * opts.query: case-insensitive substring of symbol OR name when non-empty (trimmed).
 * opts.sector: exact match when set.
 * opts.tiers: array of tiers to keep when non-empty.
 */
export function filterRecommendations(rows, opts = {}) {
  throw new Error('B1: implement filterRecommendations');
}

/**
 * Return a NEW array sorted by `key` ("rank", "score", "net_edge_bps", "symbol", ...).
 * dir: "asc" (default) or "desc". null/undefined values always go last, whatever the direction.
 */
export function sortRecommendations(rows, key = 'rank', dir = 'asc') {
  throw new Error('B1: implement sortRecommendations');
}

/**
 * One entry per sector: { sector, count, meanScore, overweight, underweight }.
 * overweight counts STRONG_OVERWEIGHT + OVERWEIGHT; underweight counts UNDERWEIGHT + AVOID.
 * Sorted by meanScore descending.
 */
export function sectorSummary(rows) {
  throw new Error('B1: implement sectorSummary');
}

/** A recommendation's contributions sorted by absolute contribution, largest first (new array). */
export function contributionsSorted(rec) {
  throw new Error('B1: implement contributionsSorted');
}

/**
 * Banner for the run's data_mode:
 * SYNTHETIC -> { show: true, tone: "warning", text: "SYNTHETIC FIXTURE — fictional instruments, generated numbers. Not results." }
 * REPLAY    -> { show: true, tone: "info", text: "REPLAY — sample data with recorded model answers." }
 * REAL      -> { show: false, tone: "none", text: "" }
 * Anything else throws.
 */
export function dataModeBanner(dataMode) {
  throw new Error('B1: implement dataModeBanner');
}
