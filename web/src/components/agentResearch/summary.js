import { contributionsSorted } from '../../lib/data.js';
import { formatCount, formatScore } from '../../lib/format.js';

// A presentation of the validated records, not a new verifier or ranking model.
export function buildGuide(record, run) {
  const { row, explanation } = record;
  const claims = explanation?.claims || [];
  const failed = claims.flatMap((claim) => claim.checks.filter((check) => check.passed === false)
    .map((check) => ({ claim, check })));
  const top = contributionsSorted(row)[0];
  const field = (label, value) => ({ label, value: value == null ? null : String(value) });
  const counts = ['verified', 'rejected'].map((status) => field(status, explanation
    ? formatCount(claims.filter((claim) => claim.status === status).length) : null));
  return {
    symbol: row.symbol,
    synthetic: run.data_mode === 'SYNTHETIC',
    temporal: claims.some((claim) => claim.checks.some((check) => check.name === 'cause_before_move')),
    sections: [
      {
        key: 'why',
        fields: [field('rank', `${formatCount(row.rank)} / ${formatCount(run.recommendations.filter((item) => item.pool === row.pool).length)}`),
          field('score', formatScore(row.score)), field('tier', row.tier),
          field('largest', top?.factor), field('contribution', top ? formatScore(top.contribution) : null)],
        notes: ['meaning'],
      },
      {
        key: 'evidence',
        fields: [field('verdict', explanation?.verdict), ...counts, field('mode', run.data_mode), field('asOf', run.as_of)],
        notes: explanation ? [] : ['noExplanation'],
        claims,
      },
      {
        key: 'risk',
        fields: [], notes: [],
        groups: [
          { label: 'counter', items: explanation?.counter_case || [] },
          { label: 'invalidation', items: row.invalidation || [] },
          { label: 'watch', items: row.what_to_watch || [] },
        ],
      },
      {
        key: 'abstain', fields: [field('verdict', explanation?.verdict)],
        notes: !explanation ? ['noExplanation'] : explanation.verdict === 'abstained'
          ? ['abstained', ...(failed.length ? [] : ['noReason'])] : ['noAbstention'],
        failed,
      },
    ],
  };
}

// Only deterministic localized text is spoken. Arbitrary source narratives stay verbatim in the UI.
export function guideSpeech(model, t, describeField = (field) => field.value) {
  return [t('title'), model.symbol, t('intro'), ...(model.synthetic ? [t('synthetic')] : []),
    ...model.sections.flatMap((section) => [t(section.key),
      ...section.fields.map((field) => `${t(field.label)}: ${describeField(field) ?? t('missing')}.`),
      ...section.notes.map(t),
      ...(section.groups || []).map((group) => `${t(group.label)}: ${formatCount(group.items.length)}.`),
      ...(section.failed?.length ? [t('checks'), ...section.failed.map(({ check }) => `${check.name}: ${t('failed')}.`)] : []),
    ]), ...(model.temporal ? [t('temporal')] : []),
  ].join('\n');
}
