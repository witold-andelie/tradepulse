// One-sentence chart summaries computed from run data (ChartFigure `summary`).
// They describe recorded values only; none of them claims a forecast or a trend that the data
// does not show.
import { formatPct } from './format.js';

const count = (value) => value.toLocaleString('en-US');
const fixed = (value, digits) => value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const signed = (value, digits) => `${value > 0 ? '+' : ''}${fixed(value, digits)}`;
const plural = (n, word) => `${count(n)} ${word}${n === 1 ? '' : 's'}`;

/** history: [{ date, points, state }] in date order. */
export function regimeHistorySummary(history, label) {
  if (!history.length) return `${label}: no recorded regime history.`;
  const latest = history[history.length - 1];
  const states = (state) => history.filter((item) => item.state === state).length;
  const peak = Math.max(...history.map((item) => item.points));
  return `${label}: ${plural(history.length, 'recorded day')} from ${history[0].date} to ${latest.date}; `
    + `the last recorded day has ${count(latest.points)} of 5 points (${latest.state}); `
    + `${count(states('elevated'))} elevated and ${count(states('stressed'))} stressed days; peak ${count(peak)} points.`;
}

/** buckets: calibration rows with n > 0 and both coordinates present. */
export function calibrationSummary(buckets) {
  if (!buckets.length) return 'All pools combined: no score bucket has settled outcomes.';
  const sorted = [...buckets].sort((a, b) => a.predicted - b.predicted);
  const total = sorted.reduce((sum, item) => sum + item.n, 0);
  const above = sorted.filter((item) => item.observed > 0.5).length;
  const lowest = sorted[0];
  const highest = sorted[sorted.length - 1];
  const ends = sorted.length === 1
    ? `the share beating the benchmark is ${formatPct(lowest.observed)}`
    : `the share beating the benchmark is ${formatPct(lowest.observed)} in the lowest-score bucket and ${formatPct(highest.observed)} in the highest`;
  return `All pools combined: ${plural(sorted.length, 'score bucket')} with ${plural(total, 'settled outcome')}; ${ends}; `
    + `${count(above)} of ${count(sorted.length)} above the 50% reference.`;
}

/** values: [{ date, ic }] for one pool; ic may be null. */
export function compositeIcSummary(values, label) {
  const known = values.map((item) => item.ic).filter((ic) => ic != null && Number.isFinite(ic));
  const missing = values.length - known.length;
  const gap = missing ? `; ${plural(missing, 'decision')} without an IC` : '';
  if (!known.length) return `${label}: no decision has a rank IC${gap}.`;
  const mean = known.reduce((sum, ic) => sum + ic, 0) / known.length;
  const positive = known.filter((ic) => ic > 0).length / known.length;
  return `${label}: ${plural(known.length, 'decision')} with a rank IC, mean ${signed(mean, 3)}, `
    + `${formatPct(positive, 0)} positive${gap}.`;
}

/** pairs: summarizeTrace pairs shown in the timeline; timing: 'reported' or 'timestamps'. */
export function timelineSummary(pairs, timing, spanMs) {
  const duration = (pair) => (timing === 'reported' ? pair.reportedMs : pair.intervalMs);
  if (!pairs.length) return 'No complete pipeline stage was recorded.';
  const longest = pairs.reduce((best, pair) => (duration(pair) > duration(best) ? pair : best));
  const failed = pairs.filter((pair) => pair.failed).length;
  const basis = timing === 'reported' ? 'reported duration' : 'timestamp interval';
  const span = spanMs == null ? '' : ` over ${fixed(spanMs / 1000, 1)} s of trace timestamps`;
  return `${plural(pairs.length, 'completed stage')}${failed ? ` (${count(failed)} failed)` : ''}${span}; `
    + `the longest by ${basis} is ${longest.start.node} (${fixed(duration(longest) / 1000, 1)} s).`;
}
