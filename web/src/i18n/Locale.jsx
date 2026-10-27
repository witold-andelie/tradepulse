import { guideLoaded } from '../components/agentResearch/messages.js';
import { createLocaleController } from './controller.js';
import { createContext, isValidElement, cloneElement, useContext, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { loadCatalog, loadGuideCatalog, messageFor, supportedLocales, translator } from './catalog.js';

const englishContext = { locale: 'en', requestedLocale: 'en', phase: 'ready', t: translator('en'), chooseLocale: () => {}, dir: 'ltr' };
const LocaleContext = createContext(englishContext);
function optionalStorage() { try { return window.localStorage; } catch { return undefined; } }
export function LocaleProvider({ children }) {
  const [controller] = useState(() => createLocaleController({ storage: optionalStorage(), load: async (id) => {
    await loadCatalog(id);
    if (window.location.pathname.startsWith('/ticker/')) await loadGuideCatalog(id);
  } }));
  const state = useSyncExternalStore(controller.subscribe, controller.getSnapshot, controller.getSnapshot);
  const { locale, phase, requestedLocale } = state;
  const value = useMemo(() => ({ ...state, t: translator(locale), dir: locale === 'ar' ? 'rtl' : 'ltr',
    chooseLocale: controller.chooseLocale, retryLocale: controller.retry, reportLocaleFailure: controller.reportFailure }), [state, controller, locale]);
  useEffect(() => { controller.start(); }, [controller]);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = value.dir;
  }, [locale, value.dir]);
  return <LocaleContext.Provider value={value}>{!state.initialComplete
    ? <main className="locale-bootstrap"><LanguageSelector /><p role="status" aria-label={value.t('Language')}>…</p></main>
    : children}</LocaleContext.Provider>;
}
export function LocaleStatus() {
  const { locale, phase, requestedLocale, failedLocale, retryLocale, t } = useLocale();
  if (phase === 'error') return <aside className="notice locale-notice" aria-label={t('Language')}><div role="alert">
    <p>{t('Language could not be loaded. English is active.')} <bdi>{supportedLocales.find((item) => item.id === failedLocale)?.name}</bdi></p>
    <button type="button" className="button" onClick={retryLocale}>{t('Retry')}</button></div></aside>;
  if (phase === 'loading') return <aside className="locale-notice" aria-label={t('Language')}><p role="status">{t('Language')} · <bdi>{supportedLocales.find((item) => item.id === requestedLocale)?.name}</bdi> …</p></aside>;
  return null;
}
export function useLocale() { return useContext(LocaleContext); }

// Named rich slots preserve complete sentence word order without HTML injection or source-text replacement.
export function Message({ text, values = {} }) {
  const { locale } = useLocale();
  const localized = messageFor(locale, text);
  return localized.split(/(\{[a-zA-Z]\w*\})/g).map((part, index) => {
    const key = /^\{([a-zA-Z]\w*)\}$/.exec(part)?.[1];
    if (!key) return part;
    const value = values[key] ?? '—';
    return isValidElement(value) ? cloneElement(value, { key: index }) : <bdi dir={/^[A-Za-z0-9+−_-]/.test(String(value)) ? "ltr" : "auto"} key={index}>{value}</bdi>;
  });
}
export function LanguageSelector() {
  const { locale, requestedLocale, phase, t, chooseLocale } = useLocale();
  return <label className="language-selector" htmlFor="app-language"><span><span aria-hidden="true">🌐 </span>{t('Language')}</span>
    <select id="app-language" value={phase === 'loading' ? requestedLocale : locale} aria-busy={phase === 'loading'} onChange={(event) => chooseLocale(event.target.value)}>
      {supportedLocales.map((item) => <option key={item.id} value={item.id} lang={item.id} dir={item.dir}>{item.name}</option>)}
    </select>
  </label>;
}
export function SourceText({ children, inline = false, label = true }) {
  const { locale, t } = useLocale();
  // An inline-compatible boundary is valid inside existing paragraphs, cells and labels.
  return <span className="original-source">{locale !== 'en' && label && <small className="source-label">{t('Original source content — not translated')}: </small>}<span lang="" dir="auto" translate="no">{children}</span></span>;
}
export function Canonical({ children }) { return <bdi dir="ltr" translate="no">{children}</bdi>; }

// Route gate prevents an English guide caveat flashing before its requested translation.
export function GuideCatalogBoundary({ children }) {
  const { locale, t, reportLocaleFailure } = useLocale();
  const [ready, setReady] = useState(() => guideLoaded(locale) ? locale : null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let current = true;
    setError(false);
    loadGuideCatalog(locale).then(() => { if (current) setReady(locale); }, () => { if (current) { setError(true); reportLocaleFailure(locale); } });
    return () => { current = false; };
  }, [locale, attempt, reportLocaleFailure]);
  if (ready === locale || guideLoaded(locale)) return children;
  return <section className="card" aria-label={t('Instrument Research')}>
    <p role={error ? 'alert' : 'status'}>{t(error ? 'Data could not be loaded. Please retry.' : 'Loading research data…')}</p>
    {error && <button type="button" className="button" onClick={() => setAttempt((value) => value + 1)}>{t('Retry')}</button>}
  </section>;
}
