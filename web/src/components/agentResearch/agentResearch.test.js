import { afterEach, describe, expect, it, vi } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { researchRecord } from '../../lib/research.js';
import { buildGuide, guideSpeech } from './summary.js';
import { isComplete, localeRegistry, lookupMessage, messages, readLocale, requiredKeys, writeLocale } from './messages.js';
import { createSpeechController, matchingVoices, speechAvailable } from './speech.js';

describe('guide-only locale boundary', () => {
  it('exposes all eleven locales only with every required translation', () => {
    expect(localeRegistry.map((item) => item.id)).toEqual(['en', 'zh-CN', 'zh-TW', 'es', 'fr', 'de', 'pt-BR', 'ja', 'ko', 'cs', 'ar']);
    for (const locale of localeRegistry) {
      expect(locale.complete).toBe(true);
      expect(Object.keys(messages[locale.id]).sort()).toEqual([...requiredKeys].sort());
    }
    expect(localeRegistry.find((item) => item.id === 'ar').dir).toBe('rtl');
  });
  it('falls back to tagged English without treating an incomplete locale as complete', () => {
    const catalog = { es: { ...messages.es, temporal: '' } };
    expect(isComplete('es', catalog)).toBe(false);
    expect(lookupMessage('es', 'temporal', catalog)).toEqual({ text: messages.en.temporal, lang: 'en' });
    expect(lookupMessage('unknown', 'why')).toEqual({ text: messages.en.why, lang: 'en' });
  });
  it('defaults to English and tolerates invalid or blocked local storage', () => {
    expect(readLocale()).toBe('en');
    expect(readLocale({ getItem: () => 'not-a-locale' })).toBe('en');
    expect(readLocale({ getItem: () => 'ar' })).toBe('ar');
    const blocked = { getItem() { throw Error('blocked'); }, setItem() { throw Error('blocked'); } };
    expect(readLocale(blocked)).toBe('en');
    expect(() => writeLocale(blocked, 'ar')).not.toThrow();
    const storage = { setItem: vi.fn() };
    writeLocale(storage, 'ja');
    expect(storage.setItem).toHaveBeenCalledWith('tradepulse.researchGuide.locale', 'ja');
  });
});

describe('recorded research without invented explanations', () => {
  const record = researchRecord(fixture, 'us_equity', 'SYN369');
  it('preserves the tier, abstention, both claim states and original evidence references', () => {
    const before = JSON.stringify(fixture);
    const model = buildGuide(record, fixture);
    expect(model.sections.map((section) => section.key)).toEqual(['why', 'evidence', 'risk', 'abstain']);
    expect(model.sections[0].fields.find((field) => field.label === 'tier').value).toBe(record.row.tier);
    expect(model.sections[1].fields[0].value).toBe('abstained');
    expect(model.sections[1].claims).toBe(record.explanation.claims);
    expect(model.sections[3].failed[0].check.name).toBe('cause_before_move');
    expect(model.temporal).toBe(true);
    for (const locale of localeRegistry) {
      const speech = guideSpeech(model, (key) => lookupMessage(locale.id, key).text);
      expect(speech).toContain(record.row.symbol);
      expect(speech).toContain(record.row.tier);
      expect(speech).toContain('abstained');
      expect(speech).not.toContain(record.explanation.claims[1].text);
    }
    expect(JSON.stringify(fixture)).toBe(before);
  });
  it('reports a recorded failure without manufacturing an event or market-move date', () => {
    const speech = guideSpeech(buildGuide(record, fixture), (key) => messages.en[key]);
    expect(speech).toContain('cannot be independently reproduced');
    expect(speech).not.toContain(fixture.created_at);
    expect(speech).toContain(messages.en.synthetic);
    // The as-of date is retained only as decision context, never presented as either missing timestamp.
    expect(buildGuide(record, fixture).sections[1].fields.find((field) => field.label === 'asOf').value).toBe(fixture.as_of);
  });
  it('handles explained, absent-explanation and unknown records distinctly', () => {
    const explained = fixture.explanations.find((item) => item.verdict === 'explained');
    const model = buildGuide(researchRecord(fixture, explained.pool, explained.symbol), fixture);
    expect(model.sections[3].notes).toEqual(['noAbstention']);
    const row = fixture.recommendations.find((item) => !item.explanation_id);
    const absent = buildGuide(researchRecord(fixture, row.pool, row.symbol), fixture);
    expect(absent.sections[1].notes).toContain('noExplanation');
    expect(absent.sections[1].fields[0].value).toBeNull();
    expect(absent.sections[1].fields.find((field) => field.label === 'verified').value).toBeNull();
    expect(absent.sections[1].fields.find((field) => field.label === 'rejected').value).toBeNull();
    expect(researchRecord(fixture, 'us_equity', 'UNKNOWN')).toBeNull();
  });
  it('does not infer an abstention reason when no failed checks were supplied', () => {
    const withoutChecks = { ...record, explanation: { ...record.explanation, claims: [] } };
    expect(buildGuide(withoutChecks, fixture).sections[3].notes).toContain('noReason');
  });
});

describe('native speech lifecycle', () => {
  afterEach(() => vi.useRealTimers());
  function setup() {
    const synth = { speak: vi.fn(), pause: vi.fn(), resume: vi.fn(), cancel: vi.fn(), getVoices: () => [] };
    const changes = vi.fn();
    class Utterance { constructor(text) { this.text = text; } }
    const controller = createSpeechController(synth, Utterance, changes);
    const voice = { name: 'English', lang: 'en-US', voiceURI: 'en-test' };
    return { synth, changes, controller, voice };
  }
  it('matches languages explicitly and does not replace a missing regional language', () => {
    const voices = [{ lang: 'en-US' }, { lang: 'ar-SA' }, { lang: 'zh-TW' }];
    expect(matchingVoices(voices, 'ar')).toEqual([voices[1]]);
    expect(matchingVoices(voices, 'zh-CN')).toEqual([]);
    expect(matchingVoices(voices, 'ja')).toEqual([]);
    expect(speechAvailable(null, undefined)).toBe(false);
  });
  it('never starts automatically and supports play, pause, resume, stop and stale-event isolation', () => {
    const { synth, changes, controller, voice } = setup();
    expect(synth.speak).not.toHaveBeenCalled();
    controller.play('Readable structured summary', voice);
    const utterance = synth.speak.mock.calls[0][0];
    expect(utterance.text).toBe('Readable structured summary');
    expect(utterance.voice).toBe(voice);
    utterance.onstart();
    controller.pause(); expect(synth.pause).toHaveBeenCalledOnce();
    controller.resume(); expect(synth.resume).toHaveBeenCalledOnce();
    const staleEnd = utterance.onend;
    controller.stop(); expect(synth.cancel).toHaveBeenCalledOnce();
    staleEnd();
    expect(changes.mock.calls.map(([status]) => status)).toEqual(['speaking', 'speaking', 'paused', 'speaking', 'idle']);
  });
  it('cancels an active utterance on disposal without notifying an unmounted component', () => {
    const { synth, changes, controller, voice } = setup();
    controller.play('Summary', voice);
    controller.dispose();
    expect(synth.cancel).toHaveBeenCalledOnce();
    expect(changes).toHaveBeenCalledTimes(1);
  });
  it('keeps an early pause through a late native start and handles native pause/resume events', () => {
    vi.useFakeTimers();
    const { synth, changes, controller, voice } = setup();
    controller.play('Summary', voice);
    controller.pause();
    vi.advanceTimersByTime(12000);
    expect(changes).toHaveBeenLastCalledWith('paused');
    const utterance = synth.speak.mock.calls[0][0];
    utterance.onstart();
    expect(changes).toHaveBeenLastCalledWith('paused');
    controller.resume();
    utterance.onpause(); expect(changes).toHaveBeenLastCalledWith('paused');
    utterance.onresume(); expect(changes).toHaveBeenLastCalledWith('speaking');
    utterance.onend(); expect(changes).toHaveBeenLastCalledWith('ended');
    controller.dispose();
  });
  it('handles browser errors, missing voices and a stalled start without breaking research', () => {
    vi.useFakeTimers();
    const { synth, changes, controller, voice } = setup();
    controller.play('Summary', null);
    expect(synth.speak).not.toHaveBeenCalled();
    expect(changes).toHaveBeenLastCalledWith('error');
    controller.play('Summary', voice);
    synth.speak.mock.calls[0][0].onerror({ error: 'interrupted' });
    expect(changes).toHaveBeenLastCalledWith('error');
    controller.play('Summary', voice);
    vi.advanceTimersByTime(12000);
    expect(synth.cancel).toHaveBeenCalled();
    expect(changes).toHaveBeenLastCalledWith('error');
  });
});
