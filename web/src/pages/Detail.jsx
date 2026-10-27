import { formatDays } from '../i18n/days.js';
import { SourceText, Canonical } from '../i18n/Locale.jsx';
import { poolName, sectorName, factorName } from '../i18n/labels.js';
import { useLocale, Message } from "../i18n/Locale.jsx";
import { Link, useLocation, useParams } from 'react-router-dom';
import { useRunOutput } from '../hooks/useRunOutput.jsx';
import { usePresentation } from '../hooks/usePresentation.jsx';
import { contributionsSorted } from '../lib/data.js';
import { researchRecord, safeMarketReturn } from '../lib/research.js';
import { formatBps, formatPct, formatScore } from '../lib/format.js';
import { Badge, Empty, Gate, Metrics, NotFound, number, PageTitle, TableScroll, TextList, Tier } from '../components/ui.jsx';
import { StanceMeaning } from '../components/ResearchGuide.jsx';
import Chart from '../components/Chart.jsx';
import GuidedResearch from '../components/agentResearch/GuidedResearch.jsx';

function Evidence({ evidence }) {
  const { t, locale } = useLocale();
  const safeUrl = evidence.url && /^https?:\/\//i.test(evidence.url) ? evidence.url : null;
  return <dl className="evidence">
    <dt>{t("Evidence ID")}</dt><dd><Canonical>{evidence.evidence_id}</Canonical></dd>
    <dt>{t("Query template")}</dt><dd><Canonical>{evidence.query_template}</Canonical></dd>
    <dt>{t("Parameters")}</dt><dd><pre>{JSON.stringify(evidence.params, null, 2)}</pre></dd>
    <dt>{t("Rows SHA-256")}</dt><dd className="hash"><Canonical>{evidence.rows_sha256}</Canonical></dd>
    <dt>{t("Source table")}</dt><dd><Canonical>{evidence.source_table}</Canonical></dd>
    <dt>{t("As of")}</dt><dd><bdi dir="ltr">{evidence.as_of}</bdi></dd>
    <dt>{t("Reference")}</dt><dd>{safeUrl ? <a className="text-link" href={safeUrl} target="_blank" rel="noreferrer noopener">{t("Open source ↗")}</a> : t("No source link supplied.")}</dd>
  </dl>;
}
function Claim({ claim }) {
  const { t, locale } = useLocale();
  return <details className={`claim ${claim.status}`}>
    <summary><Badge tone={claim.status === 'verified' ? 'positive' : 'negative'}>{claim.status === 'verified' ? t("✓ Verified") : t("✗ Rejected")}</Badge><span><SourceText inline>{claim.text}</SourceText></span><span className="muted" aria-hidden="true">＋</span></summary>
    <div className="claim-body"><p className="caption"><Canonical>{claim.claim_id}</Canonical> · <Canonical>{claim.kind}</Canonical></p><h4 className="font-semibold">{t("Recorded checks")}</h4>
      <ul className="check-list">{claim.checks.map((check, i) => <li key={i}><Gate value={check.passed} /><strong>{check.name}</strong><span><SourceText inline>{check.detail}</SourceText></span></li>)}</ul>
      {claim.checks.some((check) => check.name === 'cause_before_move') && <p className="caption">{t('guide.temporal')}</p>}
      <h4 className="font-semibold">{t("Source evidence")}</h4>{claim.evidence.length ? claim.evidence.map((item) => <Evidence key={item.evidence_id} evidence={item} />) : <p className="muted">{t("No evidence reference supplied.")}</p>}
    </div>
  </details>;
}
function ExplanationPanel({ explanation, row, synthetic }) {
  const { t, locale } = useLocale();
  return <section className="card" id="explanation" tabIndex={-1} aria-labelledby="explanation-title">
    <div className="section-heading"><div><p className="eyebrow">{t("Recorded Analyst → Skeptic → Verifier output")}</p><h2 id="explanation-title">{t("Decision explanation")}</h2></div>{explanation && <Badge tone={explanation.verdict}>{explanation.verdict}</Badge>}</div>
    {explanation ? <>
      <p className="explanation-summary"><SourceText>{explanation.summary}</SourceText></p>
      {synthetic && <p className="caption">{t('guide.synthetic')}</p>}
      <p className="section-description">{t("These are the original recorded claims and checks. A verified claim is not a guarantee of future returns. Rejected claims remain visible and must not be treated as supporting evidence.")}</p>
      {explanation.verdict === 'abstained' && <p className="notice">{t("The explanation abstained. Rejected claims are retained below for inspection; they are not supporting evidence. The explanation verdict and the original research tier are separate recorded fields.")}</p>}
      <div className="claims">{[['verified', t("Supporting claims recorded as verified")], ['rejected', t("Rejected claims — not supporting evidence")]].map(([status, heading]) => <section key={status}><h3 className="evidence-group-title">{heading}</h3>{explanation.claims.some((claim) => claim.status === status) ? explanation.claims.filter((claim) => claim.status === status).map((claim) => <Claim key={claim.claim_id} claim={claim} />) : <p className="caption">{t("None recorded.")}</p>}</section>)}</div>
      <div className="two-column mt-6"><TextList title="Counter-case" items={explanation.counter_case} /><TextList title={t("Ruled out")} items={explanation.ruled_out} /></div>
      <div className="model-line"><span><Message text="Analyst: {value1}" values={{value1: explanation.models.analyst}} /></span><span><Message text="Skeptic: {value1}" values={{value1: explanation.models.skeptic}} /></span><span><Message text="Retries: {value1}" values={{value1: number(explanation.retries)}} /></span></div><p className="caption"><Message text="Explanation ID: {value1}" values={{value1: explanation.explanation_id}} /></p>
    </> : <Empty title={row.explanation_id ? t("Explanation unavailable") : t("No explanation recorded")}>{row.explanation_id ? t("The referenced explanation is not present in this run.") : t("This instrument has a recorded ranking, but no analyst explanation was supplied.")}</Empty>}
  </section>;
}
export default function Detail({ run, pool: selectedPool, symbol: selectedSymbol } = {}) {
  const { t, locale } = useLocale();
  const { pool: routePool, symbol: routeSymbol } = useParams();
  const { data: contextRun } = useRunOutput();
  const data = run || contextRun;
  const pool = selectedPool || routePool;
  const symbol = selectedSymbol || routeSymbol;
  const { isPro, marketPath } = usePresentation();
  const location = useLocation();
  const record = researchRecord(data, pool, symbol);
  if (!record) return <NotFound title={t("Instrument not found")}>{t("This pool and symbol do not identify an instrument in the current run.")}</NotFound>;
  const { row, pool: poolSummary, explanation } = record;
  const back = safeMarketReturn(location.state?.from || marketPath, pool);
  const contributions = contributionsSorted(row);
  const factorTitle = (factor) => factorName(factor, t, data.factor_cards.find((card) => card.pool === pool && card.factor === factor)?.title || factor);
  const sum = contributions.reduce((value, item) => value + item.contribution, 0);
  const chart = {
    grid: { left: 10, right: 55, top: 12, bottom: 45, containLabel: true },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText', valueFormatter: formatScore },
    xAxis: { type: 'value', name: t("Score contribution"), nameLocation: 'middle', nameGap: 30 },
    yAxis: { type: 'category', inverse: true, data: contributions.map((item) => factorTitle(item.factor)), axisLabel: { width: 115, overflow: 'truncate' } },
    series: [{ type: 'bar', barMaxWidth: 25, label: { show: true, position: 'right', formatter: (info) => formatScore(info.value), fontSize: 13 }, data: contributions.map((item) => ({ value: item.contribution, itemStyle: { color: item.contribution < 0 ? '#954b26' : '#0b7068' } })) }],
  };
  const metrics = <Metrics items={[[t("Pool rank"), t("{value1} of {value2}", {value1: number(row.rank), value2: number(data.recommendations.filter((item) => item.pool === pool).length)})], [t("Composite score"), formatScore(row.score)], [t("Expected alpha"), formatBps(row.expected_alpha_bps)], [t("Net edge"), formatBps(row.net_edge_bps)], [t("Round-trip cost"), formatBps(row.cost_bps_round_trip)], [t("Coverage"), formatPct(row.coverage)], [t("Horizon"), formatDays(row.horizon_days, t)], [t("Pool composite IC"), formatScore(poolSummary?.composite_ic)]]} />;
  const contributionPanel = <section className="card" key="contributions" id="measurements" tabIndex={-1} aria-labelledby="contribution-title">
    <div className="section-heading"><div><p className="eyebrow">{t("Original measurements / Score decomposition")}</p><h2 id="contribution-title">{t("What drives this score?")}</h2></div><Link to={`/factors?pool=${pool}`} className="text-link">{t("Explore Factor Lab ↗")}</Link></div>
    <p className="section-description">{t("A signed contribution shows how a recorded factor enters the score. A negative contribution does not prove a negative future return. Coverage describes available data, not confidence.")}</p>
    {contributions.length ? <Chart option={chart} height={Math.max(250, contributions.length * 48 + 70)} label={t("Factor contributions ordered by absolute magnitude. Positive and negative signed values contribute to the composite score.")} /> : <Empty>{t("No contributions are supplied.")}</Empty>}
    <p className="caption"><Message text="Contributions sum to the score. Recorded sum: {value1} · Score: {value2}. Positive = teal; negative = amber; each value carries its sign." values={{value1: formatScore(sum), value2: formatScore(row.score)}} /></p>
    {Math.abs(sum - row.score) > 0.0001 && <p className="notice">{t("The recorded contribution sum differs from the score. Source values are preserved.")}</p>}
    <details className="research-details"><summary>{t("View contribution measurements")}</summary><TableScroll label={t("Underlying contribution values")}><table><thead><tr><th scope="col">{t("Factor")}</th><th scope="col">{t("Z-score")}</th><th scope="col">{t("Weight")}</th><th scope="col">{t("Contribution")}</th></tr></thead><tbody>{contributions.map((item) => <tr key={item.factor}><th scope="row">{factorTitle(item.factor)}<small className="block muted">{item.factor}</small></th><td><bdi dir="ltr">{formatScore(item.z)}</bdi></td><td><bdi dir="ltr">{formatPct(item.weight)}</bdi></td><td><bdi dir="ltr">{formatScore(item.contribution)}</bdi></td></tr>)}</tbody></table></TableScroll></details>
    <details className="research-details" open={isPro}><summary>{t("All original instrument metrics")}</summary>{metrics}<p className="caption">{t("Expected alpha and net edge are estimates in basis points, not realized returns. Score is unitless. Rank is within this pool.")}</p></details>
  </section>;
  const explanationPanel = <ExplanationPanel key="explanation" explanation={explanation} row={row} synthetic={data.data_mode === 'SYNTHETIC'} />;
  const risks = <section className="card" id="risks" tabIndex={-1} key="risks" aria-labelledby="risk-title"><div className="section-heading"><div><p className="eyebrow">{t("Limits of the research")}</p><h2 id="risk-title">{t("What could invalidate this stance?")}</h2></div></div><div className="two-column"><TextList title={t("Invalidation conditions")} items={row.invalidation} /><TextList title={t("What to watch")} items={row.what_to_watch} /></div><p className="caption"><Message text="These are the conditions recorded by the source. They are not a complete assessment of suitability or investment risk. {value1}" values={{value1: data.data_mode === 'SYNTHETIC' ? t("This is a fictional instrument with generated research records.") : t("Inspect the original source and its timing before drawing a conclusion.")}} /></p></section>;
  return <>
    <Link className="text-link" to={back}><Message text="← Back to {value1}" values={{value1: poolName(pool, t, poolSummary?.label || t('Leaderboard'))}} /></Link>
    <PageTitle eyebrow={`${poolName(pool, t, poolSummary?.label || pool)} / ${sectorName(row.sector, t)}`} title={row.symbol} action={<div className="flex flex-wrap gap-2"><Tier value={row.tier} />{row.regime_adjusted && <Badge tone="elevated">{t("Adjusted by regime")}</Badge>}</div>}><p><SourceText inline label={false}>{row.name}</SourceText></p></PageTitle>
    <section className="card detail-overview"><h2>{t("What is the recorded research stance?")}</h2><StanceMeaning tier={row.tier} /><div className="detail-context"><span><Message text="Pool: {value1}" values={{value1: poolName(pool, t, poolSummary?.label || row.pool)}} /></span><span><Message text="Source tier: {value1}" values={{value1: row.tier}} /></span><span><Message text="As of {value1}" values={{value1: data.as_of}} /></span><span><Message text="Horizon: {days}" values={{days: formatDays(row.horizon_days, t)}} /></span><span><Message text="Data mode: {value1}" values={{value1: data.data_mode}} /></span></div><p className="caption"><Message text="Run created: {value1}. The decision date is the data context, not a claim of current market freshness." values={{value1: data.created_at}} /></p></section>
    {row.tier === 'NO_CALL' && <div className="notice">{t("No call — the source run records no directional research stance. No specific reason code is supplied for this instrument. Inspect coverage, pool IC and the available explanation; no stance has been inferred.")}</div>}
    {isPro ? metrics : <Metrics items={[[t("Pool rank"), t("{value1} of {value2}", {value1: number(row.rank), value2: number(data.recommendations.filter((item) => item.pool === pool).length)})], [t("Composite score"), formatScore(row.score)]]} />}
    <nav className="detail-sections" aria-label={t("Instrument research sections")}><a className="text-link" href="#explanation">{t("Evidence and counter-case ↓")}</a><a className="text-link" href="#risks">{t("Risks and invalidation ↓")}</a><a className="text-link" href="#measurements">{t("Original measurements ↓")}</a></nav>
    <GuidedResearch key={`${data.run_id}:${pool}:${symbol}`} record={record} run={data} />
    {isPro ? [contributionPanel, explanationPanel, risks] : [explanationPanel, risks, contributionPanel]}
    <div className="hero-actions"><Link className="button" to="/trace">{t("Inspect run trace →")}</Link><Link className="text-link" to="/discover">{t("Return to Discover")}</Link></div>
  </>;
}
