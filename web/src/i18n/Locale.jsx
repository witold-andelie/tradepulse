import { createContext, isValidElement, cloneElement, useContext, useEffect, useMemo, useState } from 'react';
import { messageFor, normalizeLocale, readPreference, savePreference, supportedLocales, translator } from './catalog.js';

const englishContext = { locale: 'en', t: translator('en'), chooseLocale: () => {}, dir: 'ltr' };
const LocaleContext = createContext(englishContext);
function initialLocale() { try { return readPreference(window.localStorage); } catch { return 'en'; } }
export function LocaleProvider({ children }) {
  const [locale, setLocale] = useState(initialLocale);
  const value = useMemo(() => ({ locale, t: translator(locale), dir: locale === 'ar' ? 'rtl' : 'ltr', chooseLocale: (next) => setLocale(normalizeLocale(next)) }), [locale]);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = value.dir;
    try { savePreference(window.localStorage, locale); } catch { /* Persistence is optional. */ }
  }, [locale, value.dir]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
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
  const { locale, t, chooseLocale } = useLocale();
  return <label className="language-selector" htmlFor="app-language"><span><span aria-hidden="true">🌐 </span>{t('Language')}</span>
    <select id="app-language" value={locale} onChange={(event) => chooseLocale(event.target.value)}>
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
