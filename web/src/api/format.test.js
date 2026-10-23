import { describe, expect, it } from 'vitest';
import { formatCount } from '../lib/format.js';

describe('formatCount', () => {
  it('formats computed counts consistently in English', () => {
    expect(formatCount(1234)).toBe('1,234');
    expect(formatCount(0)).toBe('0');
  });

  it('uses a dash for missing or non-finite counts', () => {
    for (const value of [null, undefined, NaN, Infinity]) expect(formatCount(value)).toBe('—');
  });
});
