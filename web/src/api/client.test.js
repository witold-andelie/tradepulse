import { afterEach, describe, expect, it, vi } from 'vitest';
import { loadRunOutput, loadTrace, requestRun } from './client.js';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('fixture mode', () => {
  it('loads contract fixtures without fetching and isolates the run snapshot', async () => {
    vi.stubEnv('VITE_API_BASE', '');
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const run = await loadRunOutput();
    const events = await loadTrace(run.run_id);
    expect(run.data_mode).toBe('SYNTHETIC');
    expect(events.length).toBeGreaterThan(0);
    expect(events.every((event) => event.run_id === run.run_id && event.data_mode === run.data_mode)).toBe(true);
    run.warnings.length = 0;
    expect((await loadRunOutput()).warnings.length).toBeGreaterThan(0);
    expect(fetchMock).not.toHaveBeenCalled();
    await expect(requestRun({ pools: ['crypto'] })).rejects.toThrow('No API configured: showing fixtures');
  });
});

describe('API mode', () => {
  it('uses the specified endpoints, JSON body, and abort signals', async () => {
    vi.stubEnv('VITE_API_BASE', ' http://localhost:8000/// ');
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal('fetch', fetchMock);
    await loadRunOutput();
    await loadTrace('SYNTHETIC/id');
    const request = { pools: ['crypto'], as_of: '2025-01-01' };
    await requestRun(request);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      'http://localhost:8000/runs/latest',
      'http://localhost:8000/runs/SYNTHETIC%2Fid/trace',
      'http://localhost:8000/run',
    ]);
    expect(fetchMock.mock.calls[2][1]).toMatchObject({
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request),
    });
    expect(fetchMock.mock.calls.every(([, options]) => options.signal instanceof AbortSignal)).toBe(true);
  });

  it('hides server bodies and raw transport errors', async () => {
    vi.stubEnv('VITE_API_BASE', 'http://localhost:8000');
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 503 });
    vi.stubGlobal('fetch', fetchMock);
    await expect(loadRunOutput()).rejects.toThrow('HTTP 503');
    fetchMock.mockRejectedValue(new Error('SYNTHETIC internal diagnostic'));
    await expect(loadRunOutput()).rejects.toThrow('Unable to load TradePulse data. Please check the connection and try again.');
    fetchMock.mockResolvedValue({ ok: true, json: async () => { throw new SyntaxError('SYNTHETIC invalid response'); } });
    await expect(loadRunOutput()).rejects.toThrow('Unable to load TradePulse data. Please check the connection and try again.');
  });

  it('rejects a trace that is not an event array', async () => {
    vi.stubEnv('VITE_API_BASE', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }));
    await expect(loadTrace('SYNTHETIC-run')).rejects.toThrow('The trace response was invalid. Please try again.');
  });

  it.each(['load', 'trace', 'run', 'body'])('aborts %s after exactly fifteen minutes', async (kind) => {
    vi.useFakeTimers();
    vi.stubEnv('VITE_API_BASE', 'http://localhost:8000');
    let signal;
    vi.stubGlobal('fetch', vi.fn((_, options) => {
      signal = options.signal;
      if (kind === 'body') return Promise.resolve({ ok: true, json: () => new Promise(() => {}) });
      return new Promise(() => {});
    }));
    const pending = kind === 'trace' ? loadTrace('SYNTHETIC-run')
      : kind === 'run' ? requestRun({ pools: ['crypto'] }) : loadRunOutput();
    const assertion = expect(pending).rejects.toThrow('The request timed out. Please try again.');
    await vi.advanceTimersByTimeAsync(15 * 60 * 1000 - 1);
    expect(signal.aborted).toBe(false);
    await vi.advanceTimersByTimeAsync(1);
    await assertion;
    expect(signal.aborted).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('supports cancellation and does not start an already cancelled request', async () => {
    vi.stubEnv('VITE_API_BASE', 'http://localhost:8000');
    const controller = new AbortController();
    controller.abort();
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    await expect(loadRunOutput({ signal: controller.signal })).rejects.toThrow('Request cancelled');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
