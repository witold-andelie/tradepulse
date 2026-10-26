// Guide resources are independent of global application catalogs and load only
// when the research guide is requested. Source narratives stay verbatim.
import english from './locales/en.json';
import { supportedLocales, normalizeLocale } from '../../i18n/metadata.js';
import { createCachedLoader, retryJsonCatalog } from '../../i18n/resource.js';
export const LOCALE_KEY = 'tradepulse.researchGuide.locale';
export const messages = { en: english };
export const requiredKeys = Object.keys(english);
export function isComplete(locale, catalog = messages) {
  return requiredKeys.every((key) => typeof catalog[locale]?.[key] === 'string' && catalog[locale][key].trim());
}
const importers = {
  'zh-CN': (attempt) => attempt ? retryJsonCatalog(new URL('./locales/zh-CN.json?no-inline', import.meta.url).href) : import('./locales/zh-CN.json'), 'zh-TW': (attempt) => attempt ? retryJsonCatalog(new URL('./locales/zh-TW.json?no-inline', import.meta.url).href) : import('./locales/zh-TW.json'),
  es: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/es.json?no-inline', import.meta.url).href) : import('./locales/es.json'), fr: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/fr.json?no-inline', import.meta.url).href) : import('./locales/fr.json'),
  de: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/de.json?no-inline', import.meta.url).href) : import('./locales/de.json'), 'pt-BR': (attempt) => attempt ? retryJsonCatalog(new URL('./locales/pt-BR.json?no-inline', import.meta.url).href) : import('./locales/pt-BR.json'),
  ja: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/ja.json?no-inline', import.meta.url).href) : import('./locales/ja.json'), ko: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/ko.json?no-inline', import.meta.url).href) : import('./locales/ko.json'),
  cs: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/cs.json?no-inline', import.meta.url).href) : import('./locales/cs.json'), ar: (attempt) => attempt ? retryJsonCatalog(new URL('./locales/ar.json?no-inline', import.meta.url).href) : import('./locales/ar.json'),
};
const resource = createCachedLoader(importers, (value, id) => {
  if (!isComplete(id, { [id]: value }) || Object.keys(value).length !== requiredKeys.length) throw new Error('Incomplete guide catalog');
  messages[id] = value;
  return value;
}, messages);
export const loadGuide = (locale) => resource.load(normalizeLocale(locale));
export const guideLoaded = (locale) => resource.has(locale);
export const localeRegistry = supportedLocales.map((item) => ({ ...item, get complete() { return isComplete(item.id); } }));
export { normalizeLocale };
export function lookupMessage(locale, key, catalog = messages) {
  if (catalog[locale]?.[key]?.trim()) return { text: catalog[locale][key], lang: locale };
  return { text: english[key] || english.missing, lang: 'en' };
}
export function readLocale(storage) {
  try { return normalizeLocale(storage?.getItem(LOCALE_KEY)); } catch { return 'en'; }
}
export function writeLocale(storage, value) {
  try { storage?.setItem(LOCALE_KEY, normalizeLocale(value)); } catch { /* Storage is optional. */ }
}
