import { useEffect, useState } from 'react';
import { loadValidatedTrace as loadTrace } from './client.js';

export function useTrace(runId) {
  const [state, setState] = useState({ runId: null, events: [], error: null, loading: false });

  useEffect(() => {
    if (!runId) return undefined;
    const controller = new AbortController();
    setState({ runId, events: [], error: null, loading: true });
    loadTrace(runId, { signal: controller.signal }).then(
      (events) => {
        if (!controller.signal.aborted) setState({ runId, events, error: null, loading: false });
      },
      (error) => {
        if (!controller.signal.aborted) setState({ runId, events: [], error: error.message, loading: false });
      },
    );
    return () => controller.abort();
  }, [runId]);

  // Never expose a previous run's events while a new run is loading.
  if (state.runId !== runId) return { events: [], error: null, loading: Boolean(runId) };
  return { events: state.events, error: state.error, loading: state.loading };
}
