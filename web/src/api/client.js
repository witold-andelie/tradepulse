// The only boundary for API and contract-fixture data. Invalid records reject the
// entire response; they are never silently removed or replaced with made-up values.
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import schema from '@contracts/api/tradepulse.schema.json';

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(schema);
const validators = Object.fromEntries(['RunOutput', 'TraceEvent', 'RunRequest'].map((name) => [
  name, ajv.getSchema(`${schema.$id}#/$defs/${name}`),
]));
export const API_TIMEOUT_MS = 15 * 60 * 1000;

function validate(value, name) {
  const check = validators[name];
  if (!check(value)) {
    const first = check.errors?.[0];
    throw new Error(`Invalid ${name}: ${first?.instancePath || 'response'} ${first?.message || 'does not match the contract'}. No records were discarded.`);
  }
  return value;
}

export function createClient({ base = '', fetcher = (...args) => fetch(...args), timeout = API_TIMEOUT_MS } = {}) {
  const api = base.replace(/\/+$/, '');
  async function bounded(action) {
    const controller = new AbortController();
    let timer;
    try {
      return await Promise.race([
        action(controller.signal),
        new Promise((_, reject) => { timer = setTimeout(() => {
          controller.abort();
          reject(new Error('Request timed out. Please retry.'));
        }, timeout); }),
      ]);
    } catch (error) {
      if (error instanceof SyntaxError) throw new Error('Malformed JSON response. Please retry or contact the data provider.');
      if (error instanceof TypeError) throw new Error('Unable to reach the API. Check the configured service and retry. No fixture fallback was substituted.');
      throw error instanceof Error ? error : new Error('Data could not be loaded. Please retry.');
    } finally { clearTimeout(timer); }
  }
  async function json(path, options, signal) {
    const response = await fetcher(`${api}${path}`, { ...options, signal });
    if (!response.ok) throw new Error(`API request failed (HTTP ${response.status}). Please retry. No fixture fallback was substituted.`);
    return response.json();
  }
  return {
    loadRunOutput: () => bounded(async (signal) => validate(api
      ? await json('/runs/latest', {}, signal)
      : (await import('@contracts/fixtures/run_output.fixture.json')).default, 'RunOutput')),
    loadTrace: (runId) => bounded(async (signal) => {
      if (api && !/^[a-z0-9-]{8,64}$/.test(runId || '')) throw new Error('A valid run identifier is required to load its trace.');
      const events = api ? await json(`/runs/${encodeURIComponent(runId)}/trace`, {}, signal)
        : (await import('@contracts/fixtures/trace.fixture.jsonl?raw')).default.split(/\r?\n/).filter((line) => line.trim()).map((line) => JSON.parse(line));
      if (!Array.isArray(events)) throw new Error('Invalid trace: expected an array.');
      events.forEach((event) => {
        validate(event, 'TraceEvent');
        if (runId && event.run_id !== runId) throw new Error('Trace run identifier does not match the selected run.');
      });
      return events;
    }),
    requestRun: (request) => bounded(async (signal) => {
      if (!api) throw new Error('No API configured: showing fixtures');
      validate(request, 'RunRequest');
      return validate(await json('/run', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request),
      }, signal), 'RunOutput');
    }),
  };
}

export const apiBase = import.meta.env.VITE_API_BASE?.trim() || '';
const client = createClient({ base: apiBase });
export const { loadRunOutput, loadTrace, requestRun } = client;
