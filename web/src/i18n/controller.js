import { catalogLoaded, loadCatalog, normalizeLocale, readPreference, savePreference } from './catalog.js';

// Latest selection wins; stale imports may warm the cache but cannot activate or
// persist an obsolete language. English remains available without a request.
export function createLocaleController({ storage, load = loadCatalog, has = catalogLoaded } = {}) {
  const preferred = readPreference(storage);
  let state = { locale: has(preferred) ? preferred : 'en', requestedLocale: preferred,
    phase: has(preferred) ? 'ready' : 'loading', initialComplete: has(preferred), failedLocale: null };
  let generation = 0;
  let started = false;
  const listeners = new Set();
  const emit = (next) => { state = { ...state, ...next }; listeners.forEach((listener) => listener()); };
  function reportFailure(next) {
    // An older route guide may fail while a newer locale selection is pending.
    if (next !== state.requestedLocale) return;
    generation += 1;
    savePreference(storage, 'en');
    emit({ locale: 'en', requestedLocale: 'en', phase: 'error', initialComplete: true, failedLocale: next });
  }
  async function chooseLocale(value) {
    const next = normalizeLocale(value);
    const token = ++generation;
    emit({ requestedLocale: next, phase: 'loading', failedLocale: null });
    try {
      await load(next);
      if (token !== generation) return;
      savePreference(storage, next);
      emit({ locale: next, phase: 'ready', initialComplete: true });
    } catch {
      if (token !== generation) return;
      reportFailure(next);
    }
  }
  return {
    getSnapshot: () => state,
    subscribe: (listener) => { listeners.add(listener); return () => listeners.delete(listener); },
    start: () => { if (!started) { started = true; return chooseLocale(preferred); } },
    chooseLocale, reportFailure,
    retry: () => chooseLocale(state.failedLocale || state.requestedLocale),
  };
}
