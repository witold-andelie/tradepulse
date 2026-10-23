import { describe, expect, it } from 'vitest';
import { accessibleChartOption, documentTitle } from './a11y.js';

describe('accessibleChartOption', () => {
  it('adds ARIA and decal patterns without dropping the option', () => {
    const out = accessibleChartOption({ series: [{ type: 'bar' }] }, { reducedMotion: false });
    expect(out.aria).toEqual({ enabled: true, decal: { show: true } });
    expect(out.series).toEqual([{ type: 'bar' }]);
    expect(out.animation).toBe(true);
  });
  it('turns animation off under reduced motion', () => {
    expect(accessibleChartOption({ animation: true }, { reducedMotion: true }).animation).toBe(false);
  });
});

describe('documentTitle', () => {
  it('names the page and the product', () => {
    expect(documentTitle('Leaderboard')).toBe('Leaderboard · TradePulse');
    expect(documentTitle('')).toBe('TradePulse');
  });
});
