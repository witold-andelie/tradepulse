import authoredEnglish from './en.json';
import { messages as guideMessages, localeRegistry } from '../components/agentResearch/messages.js';
import zhCN from './locales/zh-CN.json';
import zhTW from './locales/zh-TW.json';
import es from './locales/es.json';
import fr from './locales/fr.json';
import de from './locales/de.json';
import ptBR from './locales/pt-BR.json';
import ja from './locales/ja.json';
import ko from './locales/ko.json';
import cs from './locales/cs.json';
import ar from './locales/ar.json';
const appMessages = { en: authoredEnglish, 'zh-CN': zhCN, 'zh-TW': zhTW, es, fr, de, 'pt-BR': ptBR, ja, ko, cs, ar };

export const supportedLocales = localeRegistry.map(({ id, name, dir }) => ({ id, name, dir }));
export const english = { ...authoredEnglish, ...Object.fromEntries(Object.entries(guideMessages.en).map(([key, value]) => [`guide.${key}`, value])) };
export const catalog = Object.fromEntries(supportedLocales.map(({ id }) => [id, {
  ...appMessages[id],
  ...Object.fromEntries(Object.entries(guideMessages[id]).map(([key, value]) => [`guide.${key}`, value])),
}]));
export function normalizeLocale(value) { return supportedLocales.some((item) => item.id === value) ? value : 'en'; }
export function patternKeys(text) { return [...new Set([...text.matchAll(/\{([a-zA-Z]\w*)\}/g)].map((match) => match[1]))].sort(); }
export function messageFor(locale, key) { return Object.hasOwn(catalog[locale] || {}, key) ? catalog[locale][key] : Object.hasOwn(english, key) ? english[key] : key; }
export function interpolate(text, values = {}) { return text.replace(/\{([a-zA-Z]\w*)\}/g, (_, key) => values[key] == null ? '—' : String(values[key])); }
// Isolate canonical ASCII parameters in Arabic sentences, including canvas/ARIA captions.
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
