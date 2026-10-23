import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { normalizeView, readView, writeView } from '../lib/viewPreference.js';

const PresentationContext = createContext(null);
function storedView() {
  try { return readView(window.localStorage); } catch { return 'simple'; }
}
export function PresentationProvider({ children }) {
  const [view, setView] = useState(storedView);
  const [marketPath, setMarketPath] = useState('/pool/us_equity');
  const chooseView = useCallback((value) => {
    const next = normalizeView(value);
    setView(next);
    try { writeView(window.localStorage, next); } catch { /* In-memory selection still works. */ }
  }, []);
  const value = useMemo(() => ({ view, isPro: view === 'pro', chooseView, marketPath, rememberMarket: setMarketPath }), [view, chooseView, marketPath]);
  return <PresentationContext.Provider value={value}>{children}</PresentationContext.Provider>;
}
export function usePresentation() {
  const value = useContext(PresentationContext);
  if (!value) throw new Error('PresentationProvider is required.');
  return value;
}
