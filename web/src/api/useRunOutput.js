import { createContext, createElement, useCallback, useContext, useEffect, useState } from 'react';
import { loadRunOutput } from './client.js';

const RunOutputContext = createContext(null);

/** One shared request keeps Page, route props and run metadata on the same snapshot. */
export function RunOutputProvider({ children }) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => {
    setState({ data: null, error: null, loading: true });
    setRevision((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadRunOutput({ signal: controller.signal }).then(
      (data) => {
        if (!controller.signal.aborted) setState({ data, error: null, loading: false });
      },
      (error) => {
        if (!controller.signal.aborted) setState({ data: null, error: error.message, loading: false });
      },
    );
    return () => controller.abort();
  }, [revision]);

  return createElement(RunOutputContext.Provider, { value: { ...state, reload } }, children);
}

export function useRunOutput() {
  const state = useContext(RunOutputContext);
  if (!state) throw new Error('useRunOutput must be used within RunOutputProvider');
  return state;
}
