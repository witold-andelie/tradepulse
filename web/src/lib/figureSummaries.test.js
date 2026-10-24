import { describe, expect, it } from 'vitest';
import fixture from '../../../contracts/fixtures/run_output.fixture.json';
import { calibrationSummary, compositeIcSummary, regimeHistorySummary, timelineSummary } from './figureSummaries.js';

describe('data-derived chart summaries', () => {
  it('summarises a regime history from its records', () => {
    const history = [
      { date: '2026-10-19', points: 1, state: 'normal' },
      { date: '2026-10-20', points: 4, state: 'stressed' },
      { date: '2026-10-21', points: 2, state: 'elevated' },
    ];
    expect(regimeHistorySummary(history, 'US equities')).toBe(
      'US equities: 3 recorded days from 2026-10-19 to 2026-10-21; the last recorded day has 2 of 5 points (elevated); '
      + '1 elevated and 1 stressed days; peak 4 points.');
    expect(regimeHistorySummary([], 'Crypto')).toBe('Crypto: no recorded regime history.');
  });

  it('matches the fixture regime counts', () => {
    const us = fixture.regimes.find((item) => item.pool === 'us_equity');
    const text = regimeHistorySummary(us.history, 'US');
    expect(text).toContain(`${us.history.length} recorded days`);
    expect(text).toContain(`the last recorded day has ${us.history.at(-1).points} of 5 points`);
  });

  it('summarises calibration buckets without calling them probabilities', () => {
    const buckets = fixture.track_record.calibration.filter((item) => item.n > 0);
    const text = calibrationSummary(buckets);
    const total = buckets.reduce((sum, item) => sum + item.n, 0);
    expect(text).toContain('All pools combined');
    expect(text).toContain(`${total} settled outcomes`);
    expect(text).not.toMatch(/probabilit|calibrat/i);
    expect(calibrationSummary([])).toContain('no score bucket');
  });

  it('reports mean IC, positive share and missing decisions', () => {
    const values = [{ date: 'a', ic: 0.1 }, { date: 'b', ic: -0.05 }, { date: 'c', ic: null }, { date: 'd', ic: 0.04 }];
    expect(compositeIcSummary(values, 'Crypto')).toBe(
      'Crypto: 3 decisions with a rank IC, mean +0.030, 67% positive; 1 decision without an IC.');
    expect(compositeIcSummary([{ date: 'a', ic: null }], 'EU')).toBe('EU: no decision has a rank IC; 1 decision without an IC.');
  });

  it('names the longest stage by the selected timing source and counts failures', () => {
    const pair = (node, reportedMs, intervalMs, failed = false) => ({ start: { node }, reportedMs, intervalMs, failed });
    const pairs = [pair('settle', 2931, 5), pair('rank', 589, 9000, true)];
    expect(timelineSummary(pairs, 'reported', 16854)).toBe(
      '2 completed stages (1 failed) over 16.9 s of trace timestamps; the longest by reported duration is settle (2.9 s).');
    expect(timelineSummary(pairs, 'timestamps', null)).toContain('the longest by timestamp interval is rank (9.0 s)');
    expect(timelineSummary([], 'reported', null)).toBe('No complete pipeline stage was recorded.');
  });
});
