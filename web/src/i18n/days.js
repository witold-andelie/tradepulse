// Unit inflection changes labels only; source durations and canonical digits stay unchanged.
export function formatDays(value, t) {
  if (!Number.isFinite(value)) return '—';
  const category = new Intl.PluralRules(t.locale || 'en').select(value);
  const count = value.toLocaleString('en-US', { maximumFractionDigits: 20 });
  return t(`Days (${category})`, { count });
}
