import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { loadRunOutput } from '../api/client.js';

const RunContext = createContext(null);
export function RunProvider({ children }) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [attempt, setAttempt] = useState(0);
  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  useEffect(() => {
    let current = true;
    setState({ data: null, error: null, loading: true });
    loadRunOutput().then((data) => {
      if (current) setState({ data, error: null, loading: false });
    }, (error) => {
      if (current) setState({ data: null, error, loading: false });
    });
    return () => { current = false; };
  }, [attempt]);
  return <RunContext.Provider value={{ ...state, retry }}>{children}</RunContext.Provider>;
}
export function useRunOutput() {
  const context = useContext(RunContext);
  if (!context) throw new Error('useRunOutput must be used inside RunProvider.');
  return context;
}
