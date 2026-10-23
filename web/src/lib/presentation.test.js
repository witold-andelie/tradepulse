import { describe, expect, it } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { readView, writeView, VIEW_KEY } from './viewPreference.js';
import { discoveryRecords, researchRecord, safeMarketReturn } from './research.js';

describe('presentation preference', () => {
  it('defaults safely and accepts only the supported modes', () => {
    for (const value of [null, '', 'unknown', 'simple']) expect(readView({ getItem: () => value })).toBe('simple');
    expect(readView({ getItem: () => 'pro' })).toBe('pro');
    expect(readView()).toBe('simple');
  });
  it('handles blocked reads and writes without blocking research', () => {
    const blocked = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
    expect(readView(blocked)).toBe('simple');
    expect(writeView(blocked, 'pro')).toBe(false);
  });
  it('stores only a normalized UI preference', () => {
    const values = new Map();
    const storage = { setItem: (key, value) => values.set(key, value), getItem: (key) => values.get(key) };
    expect(writeView(storage, 'pro')).toBe(true);
    expect(readView(storage)).toBe('pro');
    expect([...values]).toEqual([[VIEW_KEY, 'pro']]);
    writeView(storage, 'unsupported');
    expect(readView(storage)).toBe('simple');
  });
});
describe('one evidence base', () => {
  it('returns the same original instrument and explanation in both presentations', () => {
    const snapshot = JSON.stringify(fixture);
    for (const row of fixture.recommendations) {
      const record = researchRecord(fixture, row.pool, row.symbol);
      expect(record.row).toBe(row);
      if (record.explanation) {
        expect(record.explanation.pool).toBe(row.pool);
        expect(record.explanation.symbol).toBe(row.symbol);
        expect(record.explanation.explanation_id).toBe(row.explanation_id);
      }
    }
    expect(JSON.stringify(fixture)).toBe(snapshot);
  });
  it('does not attach another instrument\'s explanation or invent missing records', () => {
    const row = fixture.recommendations[0];
    const modified = { ...fixture, explanations: [{ ...fixture.explanations[0], symbol: 'OTHER' }] };
    expect(researchRecord(modified, row.pool, row.symbol).explanation).toBeNull();
    expect(researchRecord(fixture, row.pool, 'missing')).toBeNull();
  });
  it('selects only actual matching explained, abstained and no-call journeys', () => {
    const selected = discoveryRecords(fixture);
    expect(selected.explained.explanation.verdict).toBe('explained');
    expect(selected.abstained.explanation.verdict).toBe('abstained');
    expect(selected.pools).toHaveLength(fixture.pools.length);
    selected.pools.forEach((row) => expect(fixture.recommendations).toContain(row));
    if (selected.noCall) expect(selected.noCall.tier).toBe('NO_CALL');
    expect(discoveryRecords({ ...fixture, explanations: [] }).abstained).toBeNull();
  });
  it('preserves market query state but rejects unrelated or external return paths', () => {
    expect(safeMarketReturn('/pool/crypto?q=coin&page=2', 'crypto')).toBe('/pool/crypto?q=coin&page=2');
    for (const value of ['https://example.com', '//example.com', '/pool/us_equity', '/pool/crypto-extra', null]) {
      expect(safeMarketReturn(value, 'crypto')).toBe('/pool/crypto');
    }
  });
});
