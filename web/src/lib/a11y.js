// Accessibility helpers shared by every page (see "Accessibility" in web/TASK.md).

/** True when the user asked the operating system to reduce motion. */
export function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Accessible defaults merged into every ECharts option: ARIA description and decal patterns
 * (series differ by pattern, not only colour) and no animation under reduced motion.
 */
export function accessibleChartOption(option, { reducedMotion = prefersReducedMotion() } = {}) {
  return {
    ...option,
    aria: { enabled: true, decal: { show: true }, ...(option.aria || {}) },
    animation: reducedMotion ? false : option.animation ?? true,
  };
}

/** "Leaderboard · TradePulse" */
export function documentTitle(title) {
  return title ? `${title} · TradePulse` : 'TradePulse';
}
