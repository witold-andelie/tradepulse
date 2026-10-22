// Display formatting (task B1). Every number on screen goes through one of these helpers.
// A missing value (null, undefined or NaN) always renders as an em dash: "—".

/** Basis points with a sign and one decimal: 12.345 -> "+12.3 bp", -3 -> "-3.0 bp", 0 -> "0.0 bp". */
export function formatBps(value) {
  throw new Error('B1: implement formatBps');
}

/** A fraction as a percentage: 0.1234 -> "12.3%", -0.05 -> "-5.0%" (digits = decimals, default 1). */
export function formatPct(value, digits = 1) {
  throw new Error('B1: implement formatPct');
}

/** A composite score with a sign and two decimals: 1.234 -> "+1.23", -0.5 -> "-0.50", 0 -> "0.00". */
export function formatScore(value) {
  throw new Error('B1: implement formatScore');
}
