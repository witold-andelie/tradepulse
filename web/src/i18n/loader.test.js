import { describe, expect, it, vi } from 'vitest';
import { createCachedLoader } from './resource.js';
import { createLocaleController } from './controller.js';
import { LOCALE_KEY, LEGACY_LOCALE_KEY, translator, supportedLocales } from './catalog.js';
import { formatDays } from './days.js';
const deferred = () => { let resolve; let reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; };
const storage = (initial = {}) => { const values = { ...initial }; return { getItem: (key) => values[key] ?? null, setItem: (key, value) => { values[key] = value; }, values }; };

describe('validated lazy resource cache', () => {
  it('deduplicates concurrent imports and caches a successful resource', async () => {
    const gate = deferred(); const importer = vi.fn(() => gate.promise);
    const resource = createCachedLoader({ fr: importer });
    const first = resource.load('fr'); const second = resource.load('fr');
    expect(first).toBe(second); expect(resource.has('fr')).toBe(false);
    gate.resolve({ default: { title: 'Français' } });
    expect(await first).toEqual({ title: 'Français' });
    expect(await resource.load('fr')).toEqual({ title: 'Français' });
    expect(importer).toHaveBeenCalledOnce();
  });
  it('evicts rejected imports and permits an explicit retry', async () => {
    const importer = vi.fn().mockRejectedValueOnce(Error('offline')).mockResolvedValueOnce({ default: { title: 'Ready' } });
    const resource = createCachedLoader({ es: importer });
    await expect(resource.load('es')).rejects.toThrow('offline'); expect(resource.has('es')).toBe(false);
    await expect(resource.load('es')).resolves.toEqual({ title: 'Ready' }); expect(importer).toHaveBeenCalledTimes(2);
  });
  it('never activates an invalid catalog or inherited importer property', async () => {
    const resource = createCachedLoader({ ar: async () => ({ default: {} }) }, () => { throw Error('Incomplete'); });
    await expect(resource.load('ar')).rejects.toThrow('Incomplete'); expect(resource.has('ar')).toBe(false);
    await expect(resource.load('constructor')).rejects.toThrow('Unsupported');
  });
});
describe('latest-selection locale state machine', () => {
  it('starts in English without requiring any non-English import', async () => {
    const load = vi.fn(async () => ({})); const store = storage();
    const state = createLocaleController({ storage: store, load, has: (id) => id === 'en' });
    expect(state.getSnapshot()).toMatchObject({ locale: 'en', initialComplete: true });
    await state.start(); expect(load).toHaveBeenCalledExactlyOnceWith('en');
  });
  it('gates the primary interface until a saved non-English preference is ready', async () => {
    const gate = deferred(); const store = storage({ [LOCALE_KEY]: 'ar' });
    const state = createLocaleController({ storage: store, load: () => gate.promise, has: (id) => id === 'en' });
    expect(state.getSnapshot()).toMatchObject({ locale: 'en', requestedLocale: 'ar', initialComplete: false });
    const request = state.start(); gate.resolve({}); await request;
    expect(state.getSnapshot()).toMatchObject({ locale: 'ar', initialComplete: true, phase: 'ready' });
  });
  it('migrates the legacy guide preference only after successful loading', async () => {
    const gate = deferred(); const store = storage({ [LEGACY_LOCALE_KEY]: 'cs' });
    const state = createLocaleController({ storage: store, load: () => gate.promise, has: () => false });
    const request = state.start(); expect(store.values[LOCALE_KEY]).toBeUndefined();
    gate.resolve({}); await request; expect(store.values[LOCALE_KEY]).toBe('cs');
  });
  it('keeps the latest locale when imports resolve in reverse order', async () => {
    const first = deferred(); const last = deferred(); const store = storage();
    const state = createLocaleController({ storage: store, load: (id) => id === 'fr' ? first.promise : last.promise, has: () => true });
    const old = state.chooseLocale('fr'); const current = state.chooseLocale('ja');
    last.resolve({}); await current; first.resolve({}); await old;
    expect(state.getSnapshot()).toMatchObject({ locale: 'ja', requestedLocale: 'ja', phase: 'ready' });
    expect(store.values[LOCALE_KEY]).toBe('ja');
  });
  it('ignores a stale failure after switching away from an unfinished import', async () => {
    const slow = deferred(); const state = createLocaleController({ load: (id) => id === 'de' ? slow.promise : Promise.resolve({}), has: () => true });
    const old = state.chooseLocale('de'); await state.chooseLocale('en'); slow.reject(Error('offline')); await old;
    expect(state.getSnapshot()).toMatchObject({ locale: 'en', phase: 'ready', failedLocale: null });
  });
  it('shows English on failure, persists the fallback, and retries the failed request', async () => {
    const store = storage({ [LOCALE_KEY]: 'fr' });
    const load = vi.fn().mockRejectedValueOnce(Error('offline')).mockResolvedValueOnce({});
    const state = createLocaleController({ storage: store, load, has: (id) => id === 'en' });
    await state.start(); expect(state.getSnapshot()).toMatchObject({ locale: 'en', phase: 'error', failedLocale: 'fr', initialComplete: true });
    expect(store.values[LOCALE_KEY]).toBe('en');
    await state.retry(); expect(state.getSnapshot()).toMatchObject({ locale: 'fr', phase: 'ready' });
    expect(store.values[LOCALE_KEY]).toBe('fr');
  });
  it('tolerates blocked storage and keeps a successful in-memory choice', async () => {
    const blocked = { getItem() { throw Error('blocked'); }, setItem() { throw Error('blocked'); } };
    const state = createLocaleController({ storage: blocked, load: async () => ({}), has: () => true });
    await state.start(); await state.chooseLocale('ko'); expect(state.getSnapshot().locale).toBe('ko');
  });
  it('notifies subscribers and safely unsubscribes without changing source records', async () => {
    const state = createLocaleController({ load: async () => ({}), has: () => true }); const notify = vi.fn();
    const unsubscribe = state.subscribe(notify); await state.chooseLocale('zh-TW');
    expect(notify).toHaveBeenCalledTimes(2); unsubscribe(); await state.chooseLocale('zh-CN'); expect(notify).toHaveBeenCalledTimes(2);
  });
});
describe('day-unit inflection preserves canonical durations', () => {
  it.each([['es', '1 día', '5 días'], ['fr', '1 jour', '5 jours'], ['de', '1 Tag', '5 Tage'], ['pt-BR', '1 dia', '5 dias'], ['cs', '1 den', '5 dní']])('%s distinguishes one day from multiple days', (id, one, many) => {
    expect(formatDays(1, translator(id))).toBe(one); expect(formatDays(5, translator(id))).toBe(many);
  });
  it('handles Czech zero, one, few, other, fractional and dynamic values', () => {
    const t = translator('cs');
    const pairs = [[0, '0 dní'], [1, '1 den'], [2, '2 dny'], [4, '4 dny'], [5, '5 dní'], [21, '21 dní'], [100, '100 dní'], [1.5, '1.5 dne'], [0.25, '0.25 dne']];
    for (const [value, text] of pairs) expect(formatDays(value, t)).toBe(text);
    expect(formatDays(null, t)).toBe('—'); expect(formatDays(NaN, t)).toBe('—');
  });
  it('does not change numeric magnitudes in any locale, including Arabic bidi isolation', () => {
    for (const { id } of supportedLocales) for (const value of [0, 1, 2, 4, 5, 21, 100, 1.5]) {
      expect(formatDays(value, translator(id))).toContain(String(value));
    }
  });
});

describe('same-origin JSON recovery after cached ESM failures', () => {
  it('passes increasing attempts to an evicted importer without refetching success', async () => {
    const calls = [];
    const resource = createCachedLoader({ fr: async (attempt) => { calls.push(attempt); if (attempt === 0) throw Error('ESM fetch failed'); return { title: 'Français' }; } });
    await expect(resource.load('fr')).rejects.toThrow();
    await expect(resource.load('fr')).resolves.toEqual({ title: 'Français' });
    await resource.load('fr'); expect(calls).toEqual([0, 1]);
  });
});


describe('Arabic source reconciliation wording', () => {
  it('describes points out of five without a bidi-sensitive slash fraction', () => {
    const t = translator('ar');
    const key = 'Source reconciliation notice: the recorded history for {value1} has {value2} of 5 points ({value3}), while the current classification has {value4} ({value5}). The source does not reconcile these values; they are displayed unchanged.';
    const text = t(key, { value1: '2026-10-21', value2: '0', value3: 'normal', value4: '1', value5: 'normal' });
    expect(text).toContain('\u20660\u2069 من 5 نقاط');
    expect(text).not.toContain('0/5');
    expect(text).toContain('2026-10-21');
  });
});
