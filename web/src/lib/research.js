import { sortRecommendations } from './data.js';

// Select original records, never a separate set of recommendations for Simple View.
export function researchRecord(run, pool, symbol) {
  const row = run.recommendations.find((item) => item.pool === pool && item.symbol === symbol);
  if (!row) return null;
  return {
    row,
    pool: run.pools.find((item) => item.pool === pool) || null,
    explanation: run.explanations.find((item) => item.explanation_id === row.explanation_id && item.pool === pool && item.symbol === symbol) || null,
  };
}
export function discoveryRecords(run) {
  const matching = run.explanations.map((item) => researchRecord(run, item.pool, item.symbol))
    .filter((item) => item?.explanation);
  return {
    explained: matching.find((item) => item.explanation.verdict === 'explained') || null,
    abstained: matching.find((item) => item.explanation.verdict === 'abstained') || null,
    noCall: run.recommendations.find((item) => item.tier === 'NO_CALL') || null,
    pools: run.pools.map((pool) => sortRecommendations(run.recommendations.filter((item) => item.pool === pool.pool), 'rank')[0]).filter(Boolean),
  };
}
export function safeMarketReturn(candidate, pool) {
  if (typeof candidate !== 'string') return `/pool/${encodeURIComponent(pool)}`;
  const [path] = candidate.split('?');
  return path === `/pool/${encodeURIComponent(pool)}` && !candidate.includes('#') ? candidate : `/pool/${encodeURIComponent(pool)}`;
}
