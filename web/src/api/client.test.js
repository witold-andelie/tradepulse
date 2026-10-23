import { describe, expect, it, vi } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { createClient } from './client.js';

const reply = (value, status = 200) => ({ ok: status === 200, status, json: async () => value });
describe('contract data client', () => {
  it('loads all fixture records and a matching trace without a backend', async () => {
    const client = createClient();
    const run = await client.loadRunOutput();
    expect(run.recommendations).toHaveLength(fixture.recommendations.length);
    expect(run.data_mode).toBe('SYNTHETIC');
    const trace = await client.loadTrace(run.run_id);
    expect(trace.length).toBeGreaterThan(0);
    expect(trace.every((event) => event.run_id === run.run_id)).toBe(true);
    await expect(client.requestRun({ pools: ['crypto'] })).rejects.toThrow('No API configured: showing fixtures');
  });
  it.each(['SYNTHETIC', 'REPLAY', 'REAL'])('preserves %s provenance and nullable fields', async (data_mode) => {
    const value = structuredClone(fixture);
    value.data_mode = data_mode;
    value.recommendations[0].expected_alpha_bps = null;
    const result = await createClient({ base: '/api', fetcher: async () => reply(value) }).loadRunOutput();
    expect(result).toBe(value);
    expect(result.recommendations[0].expected_alpha_bps).toBeNull();
  });
  it('rejects the whole malformed run, including a single invalid record', async () => {
    const value = structuredClone(fixture);
    value.recommendations[0].tier = 'UNKNOWN';
    await expect(createClient({ base: '/api', fetcher: async () => reply(value) }).loadRunOutput()).rejects.toThrow('No records were discarded');
  });
  it('accepts contract-valid empty datasets', async () => {
    const value = { ...fixture, recommendations: [], factor_cards: [], regimes: [], explanations: [], pools: [] };
    expect((await createClient({ base: '/api', fetcher: async () => reply(value) }).loadRunOutput()).recommendations).toEqual([]);
  });
  it('reports HTTP errors without silently falling back', async () => {
    await expect(createClient({ base: '/api', fetcher: async () => reply(null, 503) }).loadRunOutput()).rejects.toThrow('HTTP 503');
  });
  it('reports unreachable services and malformed JSON', async () => {
    await expect(createClient({ base: '/api', fetcher: async () => { throw new TypeError('network'); } }).loadRunOutput()).rejects.toThrow('Unable to reach');
    await expect(createClient({ base: '/api', fetcher: async () => ({ ok: true, json: () => { throw new SyntaxError(); } }) }).loadRunOutput()).rejects.toThrow('Malformed JSON');
  });
  it('bounds calls that never resolve', async () => {
    await expect(createClient({ base: '/api', timeout: 5, fetcher: () => new Promise(() => {}) }).loadRunOutput()).rejects.toThrow('timed out');
  });
  it('uses the authorized endpoints and validates outgoing requests', async () => {
    const fetcher = vi.fn(async () => reply(fixture));
    const client = createClient({ base: '/api/', fetcher });
    await client.requestRun({ pools: ['crypto'] });
    expect(fetcher.mock.calls[0][0]).toBe('/api/run');
    expect(fetcher.mock.calls[0][1].method).toBe('POST');
    await expect(client.requestRun({ pools: ['unknown'] })).rejects.toThrow('Invalid RunRequest');
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('rejects malformed and mismatched trace responses', async () => {
    const events = await createClient().loadTrace(fixture.run_id);
    await expect(createClient({ base: '/api', fetcher: async () => reply({}) }).loadTrace(fixture.run_id)).rejects.toThrow('array');
    await expect(createClient({ base: '/api', fetcher: async () => reply(events) }).loadTrace('another-run')).rejects.toThrow('does not match');
    await expect(createClient({ base: '/api', fetcher: async () => reply([{ ...events[0], kind: 'bad' }]) }).loadTrace(fixture.run_id)).rejects.toThrow('Invalid TraceEvent');
  });
});
