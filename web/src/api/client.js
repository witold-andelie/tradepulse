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

export async function loadRunOutput() {
  throw new Error('B2: implement loadRunOutput');
}

export async function loadTrace(runId) {
  throw new Error('B2: implement loadTrace');
}

export async function requestRun(runRequest) {
  throw new Error('B2: implement requestRun');
}
