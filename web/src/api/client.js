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
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import schema from '@contracts/api/tradepulse.schema.json';

const TIMEOUT_MS = 15 * 60 * 1000;
class UserError extends Error {}

function configuredBase() {
  return (import.meta.env.VITE_API_BASE || '').trim().replace(/\/+$/, '');
}

// Fixture imports cannot be aborted, so race them against the same bounded deadline.
async function boundedCall(operation, { signal, timeout = TIMEOUT_MS } = {}) {
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
    }, timeout);
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
    if (error instanceof UserError || error instanceof ContractError) throw error;
    throw new Error('Unable to load TradePulse data. Please check the connection and try again.');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
}

async function fetchJson(path, signal, options = {}) {
  const response = await fetch(`${configuredBase()}${path}`, { ...options, signal });
  if (!response.ok) {
    throw new UserError(`TradePulse could not complete the request (HTTP ${response.status}). Please try again.`);
  }
  return response.json();
}

export async function loadRunOutput(options) {
  return boundedCall(async (signal) => {
    if (configuredBase()) return fetchJson('/runs/latest', signal);
    const { default: fixture } = await import('@contracts/fixtures/run_output.fixture.json');
    return structuredClone(fixture);
  }, options);
}

export async function loadTrace(runId, options) {
  return boundedCall(async (signal) => {
    if (configuredBase()) {
      const events = await fetchJson(`/runs/${encodeURIComponent(runId)}/trace`, signal);
      if (!Array.isArray(events)) throw new UserError('The trace response was invalid. Please try again.');
      return events;
    }
    const { default: source } = await import('@contracts/fixtures/trace.fixture.jsonl?raw');
    return parseTraceLines(source);
  }, options);
}

export async function requestRun(runRequest, options) {
  if (!configuredBase()) throw new Error('No API configured: showing fixtures');
  return boundedCall((signal) => fetchJson('/run', signal, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(runRequest),
  }), options);
}

// Huyin's schema-validating client is the application boundary. The original
// named transport functions above remain compatible with existing callers.
const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(schema);
const validators = Object.fromEntries(['RunOutput', 'TraceEvent', 'RunRequest'].map((name) => [
  name, ajv.getSchema(`${schema.$id}#/$defs/${name}`),
]));
export const API_TIMEOUT_MS = TIMEOUT_MS;
export const apiBase = configuredBase();
class ContractError extends Error {}

function validate(value, name) {
  const check = validators[name];
  if (!check(value)) {
    const first = check.errors?.[0];
    throw new ContractError(`Invalid ${name}: ${first?.instancePath || 'response'} ${first?.message || 'does not match the contract'}. No records were discarded.`);
  }
  return value;
}

export function createClient({ base = '', fetcher = (...args) => fetch(...args), timeout = API_TIMEOUT_MS } = {}) {
  if (!Number.isFinite(timeout) || timeout <= 0) throw new Error('Timeout must be finite and positive.');
  const api = base.trim().replace(/\/+$/, '');
  async function bounded(action, options) {
    try {
      return await boundedCall((signal) => action(signal), { ...options, timeout });
    } catch (error) {
      if (error instanceof ContractError || error instanceof UserError) throw error;
      throw new UserError('Data could not be loaded. Please retry.');
    }
  }
  async function json(path, options, signal) {
    let response;
    try {
      response = await fetcher(`${api}${path}`, { ...options, signal });
    } catch {
      throw new UserError('Unable to reach the API. Check the configured service and retry. No fixture fallback was substituted.');
    }
    if (!response.ok) throw new UserError(`API request failed (HTTP ${response.status}). Please retry. No fixture fallback was substituted.`);
    try {
      return await response.json();
    } catch {
      throw new UserError('Malformed JSON response. Please retry or contact the data provider.');
    }
  }
  return {
    loadRunOutput: (options) => bounded(async (signal) => validate(api
      ? await json('/runs/latest', {}, signal)
      : structuredClone((await import('@contracts/fixtures/run_output.fixture.json')).default), 'RunOutput'), options),
    loadTrace: (runId, options) => bounded(async (signal) => {
      const events = api ? await json(`/runs/${encodeURIComponent(runId)}/trace`, {}, signal)
        : parseTraceLines((await import('@contracts/fixtures/trace.fixture.jsonl?raw')).default);
      if (!Array.isArray(events)) throw new ContractError('Invalid trace: expected an array.');
      events.forEach((event) => {
        validate(event, 'TraceEvent');
        if (runId && event.run_id !== runId) throw new ContractError('Trace run identifier does not match the selected run.');
      });
      return events;
    }, options),
    requestRun: (request, options) => bounded(async (signal) => {
      if (!api) throw new UserError('No API configured: showing fixtures');
      validate(request, 'RunRequest');
      return validate(await json('/run', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request),
      }, signal), 'RunOutput');
    }, options),
  };
}

export const loadValidatedRunOutput = (options) => createClient({ base: configuredBase() }).loadRunOutput(options);
export const loadValidatedTrace = (runId, options) => createClient({ base: configuredBase() }).loadTrace(runId, options);
export const requestValidatedRun = (request, options) => createClient({ base: configuredBase() }).requestRun(request, options);
