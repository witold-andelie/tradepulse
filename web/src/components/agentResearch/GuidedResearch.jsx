import { loadGuideCatalog } from '../../i18n/catalog.js';
import { guideLoaded } from './messages.js';
import { useEffect, useMemo, useState } from 'react';
import { useLocale } from '../../i18n/Locale.jsx';
import { tierLabel } from '../../lib/tiers.js';
import { enumName, factorName } from '../../i18n/labels.js';
import { useLocation } from 'react-router-dom';
import { formatCount } from '../../lib/format.js';
import { buildGuide, guideSpeech } from './summary.js';
import { useReadAloud } from './useReadAloud.js';
import styles from './GuidedResearch.module.css';

function Identifier({ children }) { return <bdi dir="ltr" lang="en" translate="no" className={styles.identifier}>{children}</bdi>; }
function Original({ children, label }) {
  return <div className={styles.original}><p className={styles.sourceLabel}>{label}</p><div lang="" dir="auto" translate="no">{children}</div></div>;
}
export default function GuidedResearch({ record, run }) {
  const { locale, requestedLocale, t: globalT } = useLocale();
  const location = useLocation();
  const t = (key) => globalT(`guide.${key}`);
  const model = useMemo(() => buildGuide(record, run), [record, run]);
  const speech = useReadAloud(locale, `${location.key}:${requestedLocale}`);
  const [guideState, setGuideState] = useState(() => ({ locale, status: guideLoaded(locale) ? 'ready' : 'loading' }));
  const [guideAttempt, setGuideAttempt] = useState(0);
  useEffect(() => {
    let current = true;
    setGuideState({ locale, status: 'loading' });
    loadGuideCatalog(locale).then(() => { if (current) setGuideState({ locale, status: 'ready' }); },
      () => { if (current) setGuideState({ locale, status: 'error' }); });
    return () => { current = false; };
  }, [locale, guideAttempt]);
  const fieldLabel = (field) => {
    if (locale === 'en' || field.value == null) return null;
    if (field.label === 'tier') return globalT(tierLabel(field.value));
    if (field.label === 'verdict') return enumName(field.value, globalT);
    if (field.label === 'largest') return factorName(field.value, globalT);
    return null;
  };
  const describeField = (field) => {
    const label = fieldLabel(field);
    return label && label !== field.value ? `${label} (${field.value})` : field.value;
  };
  const active = ['speaking', 'paused'].includes(speech.status);
  if (!guideLoaded(locale)) return <section className={`card ${styles.guide}`} aria-label={globalT('Instrument Research')}>
    <p role={guideState.status === 'error' ? 'alert' : 'status'}>{globalT(guideState.status === 'error' ? 'Data could not be loaded. Please retry.' : 'Loading research data…')}</p>
    {guideState.status === 'error' && <button type="button" className="button" onClick={() => setGuideAttempt((value) => value + 1)}>{globalT('Retry')}</button>}
  </section>;
  return <section id="agent-research-guide" className={`card ${styles.guide}`} lang={locale} dir={locale === 'ar' ? 'rtl' : 'ltr'} aria-labelledby="agent-guide-title">
    <h2 id="agent-guide-title">{t('title')}</h2>
    <button type="button" className="button" aria-controls="guide-speech-panel" onClick={() => document.getElementById('guide-speech-title')?.focus()}>{globalT('Listen to this explanation')}</button>
    <p>{t('intro')}</p>
    {model.synthetic && <p className="notice">{t('synthetic')}</p>}
    {model.sections.map((section) => <details key={section.key} className="research-details" open={section.key === 'why' ? true : undefined}>
      <summary>{t(section.key)}</summary><div className={styles.answer}>
        {!!section.fields.length && <dl className={styles.facts}>{section.fields.map((field) => <div key={field.label}><dt>{t(field.label)}</dt><dd>{field.value == null ? t('missing') : <>{fieldLabel(field) && fieldLabel(field) !== field.value && <span>{fieldLabel(field)} · </span>}<Identifier>{field.label === 'verdict' ? JSON.stringify(field.value) : field.value}</Identifier></>}</dd></div>)}</dl>}
        {section.sourceSummary && <Original label={t('source')}><p>{section.sourceSummary}</p></Original>}
        {section.notes.map((note) => <p key={note} className={styles.note}>{t(note)}</p>)}
        {section.claims?.map((claim) => <div key={claim.claim_id}>
          <p>{claim.status === 'verified' ? '✓ ' : '✗ '}{t(claim.status)} · <Identifier>{claim.status}</Identifier></p>
          <Original label={t('source')}><p>{claim.text}</p></Original>
        </div>)}
        {section.key === 'evidence' && <a className="text-link" href="#explanation">{t('inspect')} ↓</a>}
        {section.groups?.map((group) => <div key={group.label}><h3>{t(group.label)} · <Identifier>{formatCount(group.items.length)}</Identifier></h3>
          {group.items.length ? <Original label={t('source')}><ul>{group.items.map((item, index) => <li key={index}>{item}</li>)}</ul></Original> : <p>{t('missing')}</p>}
        </div>)}
        {!!section.failed?.length && <><h3>{t('checks')}</h3><ul>{section.failed.map(({ claim, check }, index) => <li key={`${claim.claim_id}-${index}`}>
          <span>{t('failed')} · <Identifier>{check.name}</Identifier> · <Identifier>{claim.claim_id}</Identifier></span>
          <Original label={t('source')}><p>{check.detail}</p></Original>
        </li>)}</ul></>}
      </div>
    </details>)}
    {model.temporal && <p className="notice">{t('temporal')}</p>}
    <section id="guide-speech-panel" className={styles.speech} aria-labelledby="guide-speech-title"><h3 id="guide-speech-title" tabIndex={-1}>{t('speechTitle')}</h3>
      <p className="caption">{t('speechScope')}</p><p className="caption">{t('privacy')}</p>
      {!speech.supported ? <p>{t('unsupported')}</p> : <>
        <div className={styles.toolbar}><label className={styles.control} htmlFor="research-guide-voice">{t('voice')}
          <select id="research-guide-voice" dir="ltr" value={speech.voice?.voiceURI || ''} onChange={(event) => speech.chooseVoice(event.target.value)} disabled={!speech.choices.length}>
            {!speech.choices.length && <option value="">—</option>}
            {speech.choices.map((voice) => <option key={voice.voiceURI} value={voice.voiceURI} lang={voice.lang}>{voice.name} ({voice.lang})</option>)}
          </select></label><button className="button" type="button" onClick={speech.refresh}>{t('refresh')}</button></div>
        <p className="caption">{globalT('Matching voices reported by this browser: {count}. Requested language: {locale}.', {count: speech.choices.length, locale})}</p>
        {!speech.voice && <><p>{t('voiceMissing')}</p><p className="caption">{globalT('Voices come from your browser and operating system. Install a voice for the requested language in device settings, then refresh. This app cannot install voices or guarantee offline audio.')}</p></>}
        <div className={styles.buttons} role="group" aria-label={t('speechTitle')}>
          <button type="button" className="button primary" onClick={() => speech.play(guideSpeech(model, t, describeField))} disabled={!speech.voice || active}>{t('play')}</button>
          <button type="button" className="button" onClick={speech.pause} disabled={speech.status !== 'speaking'}>{t('pause')}</button>
          <button type="button" className="button" onClick={speech.resume} disabled={speech.status !== 'paused'}>{t('resume')}</button>
          <button type="button" className="button" onClick={speech.stop} disabled={!active}>{t('stop')}</button>
        </div>
      </>}
      <p role="status" aria-live="polite" aria-atomic="true" className={styles.status}>{t('status')}: {t(speech.status)}</p>
    </section>
  </section>;
}
