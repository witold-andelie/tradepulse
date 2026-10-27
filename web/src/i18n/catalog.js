import authoredEnglish from './en.json';
import { messages as guideMessages, loadGuide } from '../components/agentResearch/messages.js';
import { supportedLocales, normalizeLocale } from './metadata.js';
import { createCachedLoader, retryJsonCatalog } from './resource.js';
export { supportedLocales, normalizeLocale };
const prefixed = (guide) => Object.fromEntries(Object.entries(guide).map(([key, value]) => [`guide.${key}`, value]));
export const english = { ...authoredEnglish, ...prefixed(guideMessages.en) };
// Compatibility view for synchronous label consumers; only complete imports are registered.
export const catalog = { en: english };
const importers = {
  'zh-CN': (attempt) => attempt ? retryJsonCatalog(new URL('./locales/zh-CN.json?no-inline', import.meta.url).href) : import('./locales/zh-CN.json'), 'zh-TW': (attempt) => attempt ? retryJsonCatalog(new URL('./locales/zh-TW.json?no-inline', import.meta.url).href) : import('./locales/zh-TW.json'),
  es: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/es.json?no-inline', import.meta.url).href) : import('./locales/es.json'), fr: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/fr.json?no-inline', import.meta.url).href) : import('./locales/fr.json'),
  de: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/de.json?no-inline', import.meta.url).href) : import('./locales/de.json'), 'pt-BR': (attempt) => attempt ? retryJsonCatalog(new URL('./locales/pt-BR.json?no-inline', import.meta.url).href) : import('./locales/pt-BR.json'),
  ja: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/ja.json?no-inline', import.meta.url).href) : import('./locales/ja.json'), ko: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/ko.json?no-inline', import.meta.url).href) : import('./locales/ko.json'),
  cs: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/cs.json?no-inline', import.meta.url).href) : import('./locales/cs.json'), ar: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/ar.json?no-inline', import.meta.url).href) : import('./locales/ar.json'),
};
export function patternKeys(text) { return [...new Set([...text.matchAll(/\{([a-zA-Z]\w*)\}/g)].map((match) => match[1]))].sort(); }
const appResource = createCachedLoader(importers, (value, id) => {
  const keys = Object.keys(authoredEnglish);
  if (Object.keys(value).length !== keys.length || keys.some((key) => typeof value[key] !== 'string' || !value[key].trim() || patternKeys(value[key]).join() !== patternKeys(authoredEnglish[key]).join())) throw new Error('Incomplete application catalog');
  catalog[id] = { ...value };
  return catalog[id];
}, { en: english });
export const loadCatalog = (locale) => appResource.load(normalizeLocale(locale));
export const catalogLoaded = (locale) => appResource.has(locale);
export async function loadGuideCatalog(locale) {
  const id = normalizeLocale(locale);
  const [app, guide] = await Promise.all([loadCatalog(id), loadGuide(id)]);
  catalog[id] = { ...app, ...prefixed(guide) };
  return catalog[id];
}
export function messageFor(locale, key) { return Object.hasOwn(catalog[locale] || {}, key) ? catalog[locale][key] : Object.hasOwn(english, key) ? english[key] : key; }
export function interpolate(text, values = {}) { return text.replace(/\{([a-zA-Z]\w*)\}/g, (_, key) => values[key] == null ? '—' : String(values[key])); }
export function translator(locale) {
  return Object.assign((key, values) => {
    if (typeof key !== 'string' || !Object.hasOwn(english, key)) return key;
    const displayValues = locale === 'ar' && values ? Object.fromEntries(Object.entries(values).map(([name, value]) => [name,
      value != null && /^[A-Za-z0-9+−_-]/.test(String(value)) ? `\u2066${value}\u2069` : value,
    ])) : values;
    return interpolate(messageFor(locale, key), displayValues);
  }, { locale });
}
export const LOCALE_KEY = 'tradepulse.locale';
export const LEGACY_LOCALE_KEY = 'tradepulse.researchGuide.locale';
export function readPreference(storage) {
  try {
    const current = storage?.getItem(LOCALE_KEY);
    return normalizeLocale(current == null ? storage?.getItem(LEGACY_LOCALE_KEY) : current);
  } catch { return 'en'; }
}
export function savePreference(storage, locale) { try { storage?.setItem(LOCALE_KEY, normalizeLocale(locale)); } catch { /* Memory state remains usable. */ } }
