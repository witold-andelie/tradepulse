import { describe, expect, it } from 'vitest';
import { parseTraceLines } from './trace.js';

describe('parseTraceLines', () => {
  it('accepts blank lines and Windows line endings without reordering events', () => {
    const events = [{ seq: 2, message: 'SYNTHETIC test event' }, { seq: 1, message: 'SYNTHETIC test event' }];
    const source = `\r\n${JSON.stringify(events[0])}\r\n  \r\n${JSON.stringify(events[1])}\r\n`;
    expect(parseTraceLines(source)).toEqual(events);
  });

  it('returns an empty list for an empty trace', () => {
    expect(parseTraceLines(' \n\r\n')).toEqual([]);
  });

  it('rejects malformed events instead of silently dropping them', () => {
    expect(() => parseTraceLines('{}\nnot json')).toThrow();
  });
});
