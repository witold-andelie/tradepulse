import { afterEach, describe, expect, it, vi } from 'vitest';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { researchRecord } from '../../lib/research.js';
import { buildGuide, guideSpeech } from './summary.js';
import { localeRegistry, lookupMessage, messages } from './messages.js';
import { createSpeechController } from './speech.js';

describe('recorded abstention summaries', () => {
  const record = researchRecord(fixture, 'us_equity', 'SYN369');

  it('retains a supplied reason without claiming it is missing when checks are absent', () => {
    const source = {
      ...record,
      explanation: {
        ...record.explanation,
        summary: 'The analyst service was unavailable, so no explanation was generated.',
        claims: [],
      },
    };
    const before = JSON.stringify(source);
    const model = buildGuide(source, fixture);
    const section = model.sections.find((item) => item.key === 'abstain');
    expect(section.sourceSummary).toBe(source.explanation.summary);
    expect(section.failed).toEqual([]);
    expect(section.notes.map((key) => messages.en[key]).join(' ')).not.toContain('No specific abstention reason');
    expect(messages.en.noReason).toContain('failed-check details');
    for (const locale of localeRegistry) {
      expect(guideSpeech(model, (key) => lookupMessage(locale.id, key).text)).not.toContain(source.explanation.summary);
    }
    expect(JSON.stringify(source)).toBe(before);
  });

  it('keeps the original summary alongside recorded failures without inventing missing text', () => {
    const section = buildGuide(record, fixture).sections.find((item) => item.key === 'abstain');
    expect(section.sourceSummary).toBe(record.explanation.summary);
    expect(section.failed[0].check).toBe(record.explanation.claims[1].checks[0]);
    const empty = { ...record, explanation: { ...record.explanation, summary: '', claims: [] } };
    const emptySection = buildGuide(empty, fixture).sections.find((item) => item.key === 'abstain');
    expect(emptySection.sourceSummary).toBeNull();
    expect(emptySection.notes).toContain('noReason');
    const absent = buildGuide({ ...record, explanation: null }, fixture).sections.find((item) => item.key === 'abstain');
    expect(absent.sourceSummary).toBeNull();
    expect(absent.notes).toEqual(['noExplanation']);
  });
});

describe('speech engines that preserve pause across cancel', () => {
  afterEach(() => vi.useRealTimers());

  function engine() {
    let paused = false;
    let queued = null;
    const spoken = [];
    const start = () => {
      if (queued && !paused) { spoken.push(queued); queued.onstart?.(); }
    };
    const synth = {
      get paused() { return paused; },
      getVoices: () => [],
      speak: vi.fn((utterance) => { queued = utterance; start(); }),
      pause: vi.fn(() => { paused = true; queued?.onpause?.(); }),
      resume: vi.fn(() => { paused = false; start(); }),
      cancel: vi.fn(() => { queued = null; }),
    };
    class Utterance { constructor(text) { this.text = text; } }
    const voice = { lang: 'en-US', voiceURI: 'test-en' };
    return { synth, Utterance, voice, spoken };
  }

  it('starts a second playback after Play, Pause and Stop without a watchdog error', () => {
    vi.useFakeTimers();
    const { synth, Utterance, voice, spoken } = engine();
    const notify = vi.fn();
    const controller = createSpeechController(synth, Utterance, notify);
    controller.play('First structured summary', voice);
    controller.pause();
    controller.stop();
    expect(synth.paused).toBe(true);
    controller.play('Second structured summary', voice);
    expect(spoken.map((utterance) => utterance.text)).toEqual(['First structured summary', 'Second structured summary']);
    expect(synth.paused).toBe(false);
    vi.advanceTimersByTime(12000);
    expect(notify).toHaveBeenLastCalledWith('speaking');
    controller.dispose();
  });

  it('allows a new page controller to play after the previous page was disposed while paused', () => {
    vi.useFakeTimers();
    const { synth, Utterance, voice, spoken } = engine();
    const firstNotify = vi.fn();
    const first = createSpeechController(synth, Utterance, firstNotify);
    first.play('Previous instrument', voice);
    first.pause();
    first.dispose();
    const before = firstNotify.mock.calls.length;
    const second = createSpeechController(synth, Utterance, vi.fn());
    second.play('Next instrument', voice);
    expect(spoken.map((utterance) => utterance.text)).toEqual(['Previous instrument', 'Next instrument']);
    expect(firstNotify).toHaveBeenCalledTimes(before);
    second.dispose();
  });
});
