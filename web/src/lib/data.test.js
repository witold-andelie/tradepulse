import { describe, expect, it } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import {
  contributionsSorted, dataModeBanner, filterRecommendations, sectorSummary, sortRecommendations,
} from './data.js';

const rows = [
  { pool: 'us_equity', symbol: 'AAA', name: 'Alpha Optics', sector: 'Information Technology', rank: 2, score: 1.5, tier: 'OVERWEIGHT', net_edge_bps: 20 },
  { pool: 'us_equity', symbol: 'BBB', name: 'Beta Power', sector: 'Utilities', rank: 1, score: 2.0, tier: 'STRONG_OVERWEIGHT', net_edge_bps: null },
  { pool: 'us_equity', symbol: 'CCC', name: 'Gamma Grid', sector: 'Utilities', rank: 3, score: -1.0, tier: 'AVOID', net_edge_bps: -30 },
  { pool: 'crypto', symbol: 'DDD-USD', name: 'Delta Coin', sector: 'layer-1', rank: 1, score: 0.1, tier: 'NEUTRAL', net_edge_bps: 5 },
];

describe('filterRecommendations', () => {
  it('filters by pool, query, sector and tiers', () => {
    expect(filterRecommendations(rows, { pool: 'us_equity' }).map((r) => r.symbol)).toEqual(['AAA', 'BBB', 'CCC']);
    expect(filterRecommendations(rows, { query: '  power ' }).map((r) => r.symbol)).toEqual(['BBB']);
    expect(filterRecommendations(rows, { query: 'ccc' }).map((r) => r.symbol)).toEqual(['CCC']);
    expect(filterRecommendations(rows, { sector: 'Utilities', tiers: ['AVOID'] }).map((r) => r.symbol)).toEqual(['CCC']);
    expect(filterRecommendations(rows, {})).toHaveLength(4);
  });
  it('does not mutate the input', () => {
    const copy = JSON.stringify(rows);
    filterRecommendations(rows, { pool: 'crypto' });
    expect(JSON.stringify(rows)).toBe(copy);
  });
});

describe('sortRecommendations', () => {
  it('sorts ascending and descending with nulls last', () => {
    expect(sortRecommendations(rows.slice(0, 3), 'rank').map((r) => r.symbol)).toEqual(['BBB', 'AAA', 'CCC']);
    expect(sortRecommendations(rows.slice(0, 3), 'net_edge_bps', 'desc').map((r) => r.symbol)).toEqual(['AAA', 'CCC', 'BBB']);
    expect(sortRecommendations(rows.slice(0, 3), 'net_edge_bps', 'asc').map((r) => r.symbol)).toEqual(['CCC', 'AAA', 'BBB']);
  });
  it('returns a new array', () => {
    const input = rows.slice(0, 3);
    expect(sortRecommendations(input, 'rank')).not.toBe(input);
    expect(input.map((r) => r.symbol)).toEqual(['AAA', 'BBB', 'CCC']);
  });
});

describe('sectorSummary', () => {
  it('aggregates per sector sorted by mean score', () => {
    expect(sectorSummary(rows.slice(0, 3))).toEqual([
      { sector: 'Information Technology', count: 1, meanScore: 1.5, overweight: 1, underweight: 0 },
      { sector: 'Utilities', count: 2, meanScore: 0.5, overweight: 1, underweight: 1 },
    ]);
  });
});

describe('contributionsSorted', () => {
  it('orders by absolute contribution', () => {
    const rec = { contributions: [{ factor: 'a', contribution: 0.1 }, { factor: 'b', contribution: -0.4 }, { factor: 'c', contribution: 0.2 }] };
    expect(contributionsSorted(rec).map((c) => c.factor)).toEqual(['b', 'c', 'a']);
    expect(rec.contributions[0].factor).toBe('a');
  });
});

describe('dataModeBanner', () => {
  it('always flags synthetic and replay data', () => {
    expect(dataModeBanner('SYNTHETIC')).toEqual({ show: true, tone: 'warning', text: 'SYNTHETIC FIXTURE — fictional instruments, generated numbers. Not results.' });
    expect(dataModeBanner('REPLAY')).toEqual({ show: true, tone: 'info', text: 'REPLAY — sample data with recorded model answers.' });
    expect(dataModeBanner('REAL')).toEqual({ show: false, tone: 'none', text: '' });
    expect(() => dataModeBanner('LIVE')).toThrow();
  });
});

describe('fixture compatibility', () => {
  it('works on the contract fixture', () => {
    expect(dataModeBanner(fixture.data_mode).show).toBe(true);
    const us = filterRecommendations(fixture.recommendations, { pool: 'us_equity' });
    expect(us.length).toBeGreaterThan(400);
    const summary = sectorSummary(us);
    expect(summary.reduce((n, s) => n + s.count, 0)).toBe(us.length);
  });
});
