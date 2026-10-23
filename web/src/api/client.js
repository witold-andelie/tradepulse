// Data access (task B2). Pages never call fetch() directly; they use these functions.
//
// When VITE_API_BASE is set:
//   loadRunOutput()  -> GET  `${VITE_API_BASE}/runs/latest`          (RunOutput)
//   loadTrace(runId) -> GET  `${VITE_API_BASE}/runs/${runId}/trace`  (TraceEvent[])
//   requestRun(req)  -> POST `${VITE_API_BASE}/run` with a RunRequest body (RunOutput)
// When it is empty:
//   loadRunOutput()  -> import('@contracts/fixtures/run_output.fixture.json')
//   loadTrace()      -> import('@contracts/fixtures/trace.fixture.jsonl?raw'), one JSON object per line
//   requestRun()     -> rejects with Error('No API configured: showing fixtures')
// Every call has a 15-minute timeout (a full run takes 5-10 minutes) and throws an Error whose
// message is safe to show to the user.

import { parseTraceLines } from './trace.js';

const TIMEOUT_MS = 15 * 60 * 1000;
class UserError extends Error {}

function apiBase() {
  return (import.meta.env.VITE_API_BASE || '').trim().replace(/\/+$/, '');
}

// Fixture imports cannot be aborted, so race them against the same bounded deadline.
async function boundedCall(operation, { signal } = {}) {
  const controller = new AbortController();
  let timer;
  let cancel;
  const interrupted = new Promise((_, reject) => {
    cancel = () => {
      controller.abort();
      reject(new UserError('Request cancelled. Please try again.'));
    };
    timer = setTimeout(() => {
      controller.abort();
      reject(new UserError('The request timed out. Please try again.'));
    }, TIMEOUT_MS);
    if (signal?.aborted) cancel();
    else signal?.addEventListener('abort', cancel, { once: true });
  });

  try {
    return await Promise.race([
      interrupted,
      Promise.resolve().then(() => {
        if (controller.signal.aborted) throw new UserError('Request cancelled. Please try again.');
        return operation(controller.signal);
      }),
    ]);
  } catch (error) {
    if (error instanceof UserError) throw error;
    throw new Error('Unable to load TradePulse data. Please check the connection and try again.');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
}

async function fetchJson(path, signal, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, { ...options, signal });
  if (!response.ok) {
    throw new UserError(`TradePulse could not complete the request (HTTP ${response.status}). Please try again.`);
  }
  return response.json();
}

export async function loadRunOutput(options) {
  return boundedCall(async (signal) => {
    if (apiBase()) return fetchJson('/runs/latest', signal);
    const { default: fixture } = await import('@contracts/fixtures/run_output.fixture.json');
    return structuredClone(fixture);
  }, options);
}

export async function loadTrace(runId, options) {
  return boundedCall(async (signal) => {
    if (apiBase()) {
      const events = await fetchJson(`/runs/${encodeURIComponent(runId)}/trace`, signal);
      if (!Array.isArray(events)) throw new UserError('The trace response was invalid. Please try again.');
      return events;
    }
    const { default: source } = await import('@contracts/fixtures/trace.fixture.jsonl?raw');
    return parseTraceLines(source);
  }, options);
}

export async function requestRun(runRequest, options) {
  if (!apiBase()) throw new Error('No API configured: showing fixtures');
  return boundedCall((signal) => fetchJson('/run', signal, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(runRequest),
  }), options);
}
