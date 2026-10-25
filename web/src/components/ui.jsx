import { SourceText, Canonical } from '../i18n/Locale.jsx';
import { enumName } from '../i18n/labels.js';
import { errorSummary } from '../i18n/errors.js';
import { useLocale, Message } from "../i18n/Locale.jsx";
import { useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { tierLabel, tierTone } from '../lib/tiers.js';

const initialHistoryKey = typeof window === 'undefined' ? 'default' : window.history.state?.key || 'default';
export const number = (value, digits = 0) => value == null || !Number.isFinite(value) ? '—' : value.toLocaleString('en-US', { maximumFractionDigits: digits });
export const tickerPath = (row) => `/ticker/${encodeURIComponent(row.pool)}/${encodeURIComponent(row.symbol)}`;
const toneClasses = {
  'strong-positive': 'tone-strong-positive', positive: 'tone-positive', neutral: 'tone-neutral',
  negative: 'tone-negative', 'strong-negative': 'tone-strong-negative', muted: 'tone-muted',
  normal: 'tone-normal', elevated: 'tone-elevated', stressed: 'tone-stressed',
  ACTIVE: 'tone-ACTIVE', MEASURED_ONLY: 'tone-MEASURED_ONLY', INSUFFICIENT_DATA: 'tone-INSUFFICIENT_DATA',
  explained: 'tone-explained', abstained: 'tone-abstained',
};
export function Badge({ children, tone = 'muted' }) { const { t } = useLocale(); return <span className={`badge ${toneClasses[tone] || toneClasses.muted}`}>{typeof children === 'string' ? enumName(children, t) : children}</span>; }
export function Tier({ value }) {
  const { t, locale } = useLocale(); return <Badge tone={tierTone(value)}>{t(tierLabel(value))}</Badge>; }
export function Gate({ value }) {
  const { t, locale } = useLocale(); return <span className={value === false ? 'negative' : value === true ? 'positive' : 'muted'}>{value == null ? t("– Not evaluated") : value ? t("✓ Passed") : t("✗ Failed")}</span>; }
export function PageTitle({ eyebrow = 'Research workspace', title, children, action }) {
  const { t, locale } = useLocale();
  const titleRef = useRef(null);
  const location = useLocation();
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      if (location.key === initialHistoryKey && !location.hash) return;
      const active = document.activeElement;
      if (active && ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'SUMMARY'].includes(active.tagName)) return;
      const target = location.hash ? document.getElementById(location.hash.slice(1)) : null;
      (target || titleRef.current)?.focus({ preventScroll: true });
      if (target) target.scrollIntoView({ block: 'start' });
    });
    return () => cancelAnimationFrame(frame);
  }, [title, location.pathname, location.hash]);
  return <div className="page-title"><div><p className="eyebrow">{typeof eyebrow === 'string' ? t(eyebrow) : eyebrow}</p><h1 ref={titleRef} tabIndex={-1} id="page-title">{title}</h1>{children && <div className="subtitle">{children}</div>}</div>{action}</div>;
}
export function Empty({ title = 'No data available', children, action }) {
  const { t, locale } = useLocale(); return <div className="empty"><span aria-hidden="true" className="empty-symbol">∅</span><h2>{t(title)}</h2><div className="muted">{children}</div>{action}</div>; }
export function NotFound({ title = 'Page not found', children }) {
  const { t, locale } = useLocale(); return <><PageTitle eyebrow={t("Unavailable destination")} title={t(title)} /><section className="card"><Empty title={t(title)} action={<Link className="button primary" to="/">{t("Return to leaderboard")}</Link>}>{children || t("This destination is not part of the current research run.")}</Empty></section></>; }
export function Loading() {
  const { t, locale } = useLocale(); return <div aria-busy="true" role="status" className="space-y-5"><span className="muted">{t("Loading research data…")}</span><div className="skeleton h-24" /><div className="grid grid-cols-2 gap-4"><div className="skeleton h-36" /><div className="skeleton h-36" /></div><div className="skeleton h-72" /></div>; }
export function ErrorState({ error, retry }) {
  const { t, locale } = useLocale(); const message = typeof error === 'string' ? error : error.message;
  return <section className="card" role="alert"><Empty title={t("Research data is unavailable")} action={<button className="button primary" onClick={retry}>{t("Retry")}</button>}><p>{errorSummary(message, t)}</p>{locale !== 'en' && <details><summary>{t('Original technical diagnostic — not translated')}</summary><SourceText>{message}</SourceText></details>}</Empty></section>; }
export function Metrics({ items }) {
  const { t, locale } = useLocale(); return <dl className="metrics">{items.map(([label, value]) => <div key={label}><dt>{t(label)}</dt><dd><Canonical>{value}</Canonical></dd></div>)}</dl>; }
export function TextList({ title, items }) {
  const { t, locale } = useLocale(); return <section><h3>{t(title)}</h3>{items.length ? <ul className="text-list">{items.map((text, i) => <li key={i}><SourceText>{text}</SourceText></li>)}</ul> : <p className="muted">{t("None recorded.")}</p>}</section>; }
export function TableScroll({ children, label }) {
  const { t, locale } = useLocale(); return <div className="table-scroll" role="region" aria-label={t(label)} tabIndex={0}>{children}</div>; }
