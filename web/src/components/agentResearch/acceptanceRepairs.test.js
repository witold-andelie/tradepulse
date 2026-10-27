import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { Badge, TableScroll } from '../ui.jsx';
import { Message } from '../../i18n/Locale.jsx';
import fixture from '@contracts/fixtures/run_output.fixture.json';
import { researchRecord } from '../../lib/research.js';
import { buildGuide, guideSpeech } from './summary.js';
import { messages } from './messages.js';
import { createSpeechController, matchingVoices } from './speech.js';

const h = React.createElement;

describe('acceptance repair boundaries', () => {
  it('names a business table without changing headers or measurements', () => {
    const table = h('table', null, h('thead', null, h('tr', null, h('th', { scope: 'col' }, 'Score'))), h('tbody', null, h('tr', null, h('td', null, '-0.05'))));
    const html = renderToStaticMarkup(h(TableScroll, { label: 'Underlying contribution values' }, table));
    expect(html).toContain('<caption class="sr-only">Underlying contribution values</caption>');
    expect(html).toContain('<th scope="col">Score</th>');
    expect(html).toContain('<td>-0.05</td>');
  });
  it('preserves an existing caption', () => {
    const html = renderToStaticMarkup(h(TableScroll, { label: 'Scores' }, h('table', null, h('caption', null, 'Original caption'), h('tbody'))));
    expect(html.match(/<caption/g)).toHaveLength(1);
    expect(html).toContain('Original caption');
  });
  it('keeps the rich badge phrase in one inline flow', () => {
    const html = renderToStaticMarkup(h(Badge, { tone: 'stressed' }, h(Message, { text: '{state} regime', values: { state: 'stressed' } })));
    expect(html).toContain('class="badge tone-stressed"><span><bdi dir="ltr">stressed</bdi> regime</span>');
  });
  it('accepts BCP-47 script tags without substituting regions', () => {
    const voices = ['zh-Hans-CN', 'zh-Hant-TW', 'pt-BR', 'pt-PT', 'es-MX', 'es-ES', 'cs_CZ', 'ar-EG'].map((lang) => ({ lang }));
    expect(matchingVoices(voices, 'zh-CN').map((v) => v.lang)).toEqual(['zh-Hans-CN']);
    expect(matchingVoices(voices, 'zh-TW').map((v) => v.lang)).toEqual(['zh-Hant-TW']);
    expect(matchingVoices(voices, 'pt-BR').map((v) => v.lang)).toEqual(['pt-BR']);
    expect(matchingVoices(voices, 'es').map((v) => v.lang)).toEqual(['es-MX', 'es-ES']);
    expect(matchingVoices(voices, 'cs').map((v) => v.lang)).toEqual(['cs_CZ']);
    expect(matchingVoices(voices, 'ar').map((v) => v.lang)).toEqual(['ar-EG']);
  });
  it('recovers a paused engine only after explicit Play', () => {
    let paused = false;
    const spoken = [];
    const synth = { get paused() { return paused; }, getVoices: () => [],
      speak: vi.fn((u) => { if (!paused) { spoken.push(u.text); u.onstart?.(); } }),
      pause: () => { paused = true; }, resume: () => { paused = false; }, cancel: vi.fn(),
    };
    class Utterance { constructor(text) { this.text = text; } }
    const controller = createSpeechController(synth, Utterance, vi.fn());
    expect(spoken).toEqual([]);
    controller.play('First', { lang: 'en-US' }); controller.pause(); controller.stop();
    expect(paused).toBe(true);
    controller.play('Second', { lang: 'en-US' });
    expect(spoken).toEqual(['First', 'Second']);
    controller.dispose();
  });
});


describe('source-only abstention reasons preserved from the lead review', () => {
  const original = researchRecord(fixture, 'us_equity', 'SYN369');
  it('keeps a supplied summary when no failed-check details are supplied', () => {
    const record = { ...original, explanation: { ...original.explanation, claims: [] } };
    const model = buildGuide(record, fixture);
    const section = model.sections.find((item) => item.key === 'abstain');
    expect(section.sourceSummary).toBe(record.explanation.summary);
    expect(section.failed).toEqual([]);
    expect(section.notes.map((key) => messages.en[key]).join(' ')).not.toContain('No specific abstention reason');
    expect(guideSpeech(model, (key) => messages.en[key])).not.toContain(record.explanation.summary);
  });
  it('distinguishes an empty summary and an absent explanation without creating a reason', () => {
    const empty = { ...original, explanation: { ...original.explanation, summary: '', claims: [] } };
    const section = buildGuide(empty, fixture).sections.find((item) => item.key === 'abstain');
    expect(section.sourceSummary).toBeNull();
    expect(section.notes).toContain('noReason');
    const absent = buildGuide({ ...original, explanation: null }, fixture).sections.find((item) => item.key === 'abstain');
    expect(absent.sourceSummary).toBeNull();
    expect(absent.notes).toEqual(['noExplanation']);
  });
});
