import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { catalog, english, interpolate, LEGACY_LOCALE_KEY, LOCALE_KEY, patternKeys, readPreference, savePreference, supportedLocales, translator } from './catalog.js';
import { Canonical, LocaleProvider, Message, SourceText } from './Locale.jsx';
import { displayVocabulary, enumName, factorName, poolName, sectorName, stageName } from './labels.js';
import { errorSummary } from './errors.js';
import { researchRecord } from '../lib/research.js';
import { buildGuide, guideSpeech } from '../components/agentResearch/summary.js';
import { regimeHistorySummary, calibrationSummary, compositeIcSummary, timelineSummary } from '../lib/figureSummaries.js';

afterEach(() => vi.unstubAllGlobals());
const store = (values = {}) => ({ getItem: (key) => values[key] ?? null, setItem: (key, value) => { values[key] = value; } });

describe('one complete global catalog', () => {
  it('contains every required nonempty app and guide message for all eleven locales', () => {
    expect(supportedLocales.map((item) => item.id)).toEqual(['en', 'zh-CN', 'zh-TW', 'es', 'fr', 'de', 'pt-BR', 'ja', 'ko', 'cs', 'ar']);
    for (const { id } of supportedLocales) {
      expect(Object.keys(catalog[id]).sort(), id).toEqual(Object.keys(english).sort());
      for (const [key, value] of Object.entries(catalog[id])) expect(typeof value === 'string' && value.trim().length > 0, `${id}: ${key}`).toBe(true);
    }
  });
  it('preserves all named placeholders and resolves every authored template', () => {
    for (const { id } of supportedLocales) for (const [key, text] of Object.entries(english)) {
      expect(patternKeys(catalog[id][key]), `${id}: ${key}`).toEqual(patternKeys(text));
      const parameters = Object.fromEntries(patternKeys(text).map((name, index) => [name, String(index + 1)]));
      expect(translator(id)(key, parameters)).not.toMatch(/\{[a-zA-Z]\w*\}/);
    }
  });
  it('includes the complete explicit display vocabulary', () => {
    for (const label of displayVocabulary) expect(Object.hasOwn(english, label), label).toBe(true);
  });
  it('does not interpolate or translate unregistered source text, even with braces or prototype-like keys', () => {
    const narrative = 'Unapproved source text {event_date}';
    expect(translator('ar')(narrative, { event_date: 'invented' })).toBe(narrative);
    expect(translator('ja')('constructor')).toBe('constructor');
    expect(translator('en')('Score')).toBe('Score');
    expect(interpolate('{count} / {total}', { count: 0, total: 5 })).toBe('0 / 5');
  });
});
describe('global preference with optional storage', () => {
  it('defaults to English and migrates the guide preference only when the global preference is absent', () => {
    expect(readPreference()).toBe('en');
    expect(readPreference(store({ [LEGACY_LOCALE_KEY]: 'ja' }))).toBe('ja');
    expect(readPreference(store({ [LEGACY_LOCALE_KEY]: 'ar', [LOCALE_KEY]: 'fr' }))).toBe('fr');
    expect(readPreference(store({ [LEGACY_LOCALE_KEY]: 'ar', [LOCALE_KEY]: 'invalid' }))).toBe('en');
  });
  it('normalizes writes and tolerates blocked reads and writes', () => {
    const storage = store(); savePreference(storage, 'cs'); expect(readPreference(storage)).toBe('cs');
    savePreference(storage, 'invalid'); expect(readPreference(storage)).toBe('en');
    const blocked = { getItem() { throw Error('blocked'); }, setItem() { throw Error('blocked'); } };
    expect(readPreference(blocked)).toBe('en');
    expect(() => savePreference(blocked, 'ar')).not.toThrow();
  });
});
describe('source and financial boundaries', () => {
  it('keeps an arbitrary source narrative verbatim and labels its original language boundary', () => {
    vi.stubGlobal('window', { localStorage: store({ [LOCALE_KEY]: 'ja' }) });
    const text = 'API connection {value1} — source narrative';
    const html = renderToStaticMarkup(React.createElement(LocaleProvider, null, React.createElement(SourceText, null, text)));
    expect(html).toContain(text);
    expect(html).toContain('lang="" dir="auto" translate="no"');
    expect(html).toContain(catalog.ja['Original source content — not translated']);
    expect(html).not.toContain(catalog.ja['API connection']);
  });
  it('supports language-specific rich interpolation order without changing numeric values', () => {
    vi.stubGlobal('window', { localStorage: store({ [LOCALE_KEY]: 'ja' }) });
    const html = renderToStaticMarkup(React.createElement(LocaleProvider, null, React.createElement(Message, {
      text: 'Showing {value1}–{value2} of {value3}', values: { value1: 1, value2: 50, value3: 520 },
    })));
    expect(html.indexOf('520')).toBeLessThan(html.indexOf('50</bdi>'));
    expect(html).toContain('dir="ltr"');
  });
  it('keeps signed canonical values isolated for RTL presentation', () => {
    expect(renderToStaticMarkup(React.createElement(Canonical, null, '-1.23'))).toContain('dir="ltr" translate="no">-1.23');
    expect(translator('ar')('As of {value1}', { value1: '2026-10-21' })).toContain('\u20662026-10-21\u2069');
  });
  it('changes only labels and keeps unknown structured codes unchanged', () => {
    const before = JSON.stringify(fixture);
    for (const { id } of supportedLocales) {
      const t = translator(id);
      expect(poolName('us_equity', t)).toBe(t('US equities'));
      expect(enumName('constructor', t)).toBe('constructor');
      expect(factorName('unknown_factor', t)).toBe('unknown_factor');
      expect(stageName('unknown_stage', t)).toBe(id === 'en' ? 'unknown stage' : 'unknown_stage');
      expect(sectorName('Unlisted sector', t)).toBe('Unlisted sector');
    }
    expect(JSON.stringify(fixture)).toBe(before);
  });
  it('connects narration to the same locale catalog without speaking arbitrary Agent narratives', () => {
    const record = researchRecord(fixture, 'us_equity', 'SYN369');
    for (const { id } of supportedLocales) {
      const t = translator(id);
      const speech = guideSpeech(buildGuide(record, fixture), (key) => t(`guide.${key}`));
      expect(speech).toContain(catalog[id]['guide.title']);
      expect(speech).toContain(record.row.tier);
      expect(speech).toContain('abstained');
      expect(speech).not.toContain(record.explanation.claims[1].text);
    }
  });
  it('localizes descriptive chart summaries while preserving canonical dates and recorded numbers', () => {
    const t = translator('zh-CN');
    const regime = fixture.regimes[0];
    const summary = regimeHistorySummary(regime.history, 'US equities', t);
    expect(summary).toContain(regime.history[0].date);
    expect(summary).toContain(regime.history.at(-1).date);
    expect(calibrationSummary([], t)).toBe(t('All pools combined: no score bucket has settled outcomes.'));
    expect(compositeIcSummary([{ date: '2026-10-21', ic: null }], 'US equities', t)).toContain('1');
    expect(timelineSummary([], 'reported', null, t)).toBe(t('No complete pipeline stage was recorded.'));
  });
  it('localizes client-owned errors without changing the API transport or source diagnostics', () => {
    const t = translator('es');
    expect(errorSummary('Unable to reach the API. Check the configured service and retry. No fixture fallback was substituted.', t)).toBe(catalog.es['Unable to reach the API. Check the configured service and retry. No fixture fallback was substituted.']);
    expect(errorSummary('API request failed (HTTP 503). Please retry. No fixture fallback was substituted.', t)).toContain('503');
    expect(errorSummary('raw original diagnostic', translator('en'))).toBe('raw original diagnostic');
  });
});
