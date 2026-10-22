import { describe, expect, it } from 'vitest';
import { formatBps, formatPct, formatScore } from './format.js';
import { TIER_ORDER, tierLabel, tierTone } from './tiers.js';

describe('formatBps', () => {
  it('formats with sign and one decimal', () => {
    expect(formatBps(12.345)).toBe('+12.3 bp');
    expect(formatBps(-3)).toBe('-3.0 bp');
    expect(formatBps(0)).toBe('0.0 bp');
  });
  it('renders missing values as a dash', () => {
    expect(formatBps(null)).toBe('—');
    expect(formatBps(undefined)).toBe('—');
    expect(formatBps(Number.NaN)).toBe('—');
  });
});

describe('formatPct', () => {
  it('converts fractions to percent', () => {
    expect(formatPct(0.1234)).toBe('12.3%');
    expect(formatPct(-0.05)).toBe('-5.0%');
    expect(formatPct(0.5, 0)).toBe('50%');
    expect(formatPct(null)).toBe('—');
  });
});

describe('formatScore', () => {
  it('formats with sign and two decimals', () => {
    expect(formatScore(1.234)).toBe('+1.23');
    expect(formatScore(-0.5)).toBe('-0.50');
    expect(formatScore(0)).toBe('0.00');
    expect(formatScore(undefined)).toBe('—');
  });
});

describe('tiers', () => {
  it('labels every tier', () => {
    expect(TIER_ORDER.map(tierLabel)).toEqual([
      'Strong overweight', 'Overweight', 'Neutral', 'Underweight', 'Avoid', 'No call',
    ]);
  });
  it('maps tones', () => {
    expect(TIER_ORDER.map(tierTone)).toEqual([
      'strong-positive', 'positive', 'neutral', 'negative', 'strong-negative', 'muted',
    ]);
  });
  it('throws on unknown tiers', () => {
    expect(() => tierLabel('BUY')).toThrow();
    expect(() => tierTone('SELL')).toThrow();
  });
});
