import { afterEach, describe, expect, it, vi } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { createClient, loadValidatedRunOutput } from './client.js';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe('integrated application data boundary', () => {
  it('isolates strict fixture snapshots between consumers', async () => {
    const client = createClient();
    const first = await client.loadRunOutput();
    const original = first.recommendations[0].symbol;
    first.recommendations[0].symbol = 'SYNTHETIC-MUTATED';
    first.warnings.length = 0;
    const second = await client.loadRunOutput();
    expect(second.recommendations[0].symbol).toBe(original);
    expect(second.warnings).toEqual(fixture.warnings);
  });

  it('cancels strict requests and never starts an already cancelled request', async () => {
    let transportSignal;
    const fetcher = vi.fn((_, options) => {
      transportSignal = options.signal;
      return new Promise(() => {});
    });
    const client = createClient({ base: '/api', fetcher });
    const cancelled = new AbortController();
    cancelled.abort();
    await expect(client.loadRunOutput({ signal: cancelled.signal })).rejects.toThrow('Request cancelled');
    expect(fetcher).not.toHaveBeenCalled();

    const controller = new AbortController();
    const pending = client.loadRunOutput({ signal: controller.signal });
    const rejected = expect(pending).rejects.toThrow('Request cancelled');
    await Promise.resolve();
    controller.abort();
    await rejected;
    expect(transportSignal.aborted).toBe(true);
  });

  it('rejects invalid API records on the actual UI entry point without fixture fallback', async () => {
    vi.stubEnv('VITE_API_BASE', ' /api/// ');
    const invalid = structuredClone(fixture);
    invalid.recommendations[0].tier = 'SYNTHETIC_INVALID_TIER';
    const fetcher = vi.fn(async () => ({ ok: true, json: async () => invalid }));
    vi.stubGlobal('fetch', fetcher);
    await expect(loadValidatedRunOutput()).rejects.toThrow('Invalid RunOutput');
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher.mock.calls[0][0]).toBe('/api/runs/latest');
  });
});
