import { Link, useLocation, useParams } from 'react-router-dom';
import { useRunOutput } from '../hooks/useRunOutput.jsx';
import { usePresentation } from '../hooks/usePresentation.jsx';
import { contributionsSorted } from '../lib/data.js';
import { researchRecord, safeMarketReturn } from '../lib/research.js';
import { formatBps, formatPct, formatScore } from '../lib/format.js';
import { Badge, Empty, Gate, Metrics, NotFound, number, PageTitle, TableScroll, TextList, Tier } from '../components/ui.jsx';
import { StanceMeaning } from '../components/ResearchGuide.jsx';
import Chart from '../components/Chart.jsx';

function Evidence({ evidence }) {
  const safeUrl = evidence.url && /^https?:\/\//i.test(evidence.url) ? evidence.url : null;
  return <dl className="evidence">
    <dt>Evidence ID</dt><dd>{evidence.evidence_id}</dd>
    <dt>Query template</dt><dd>{evidence.query_template}</dd>
    <dt>Parameters</dt><dd><pre>{JSON.stringify(evidence.params, null, 2)}</pre></dd>
    <dt>Rows SHA-256</dt><dd className="hash">{evidence.rows_sha256}</dd>
    <dt>Source table</dt><dd>{evidence.source_table}</dd>
    <dt>As of</dt><dd>{evidence.as_of}</dd>
    {safeUrl && <><dt>Reference</dt><dd><a className="text-link" href={safeUrl} target="_blank" rel="noreferrer noopener">Open source ↗</a></dd></>}
  </dl>;
}
function Claim({ claim }) {
  return <details className={`claim ${claim.status}`}>
    <summary><Badge tone={claim.status === 'verified' ? 'positive' : 'negative'}>{claim.status === 'verified' ? '✓ Verified' : '✗ Rejected'}</Badge><span>{claim.text}</span><span className="muted" aria-hidden="true">＋</span></summary>
    <div className="claim-body"><p className="caption">{claim.claim_id} · {claim.kind}</p><h4 className="font-semibold">Deterministic checks</h4>
      <ul className="check-list">{claim.checks.map((check, i) => <li key={i}><Gate value={check.passed} /><strong>{check.name}</strong><span>{check.detail}</span></li>)}</ul>
      <h4 className="font-semibold">Source evidence</h4>{claim.evidence.length ? claim.evidence.map((item) => <Evidence key={item.evidence_id} evidence={item} />) : <p className="muted">No evidence reference supplied.</p>}
    </div>
  </details>;
}
function ExplanationPanel({ explanation, row }) {
  return <section className="card" id="explanation" tabIndex={-1} aria-labelledby="explanation-title">
    <div className="section-heading"><div><p className="eyebrow">Recorded Analyst → Skeptic → Verifier output</p><h2 id="explanation-title">Decision explanation</h2></div>{explanation && <Badge tone={explanation.verdict}>{explanation.verdict}</Badge>}</div>
    {explanation ? <>
      <p className="explanation-summary">{explanation.summary}</p>
      <p className="section-description">These are the original recorded claims and checks. A verified claim is not a guarantee of future returns. Rejected claims remain visible and must not be treated as supporting evidence.</p>
      {explanation.verdict === 'abstained' && <p className="notice">The explanation abstained. Rejected claims are retained below for inspection; they are not supporting evidence. The explanation verdict and the original research tier are separate recorded fields.</p>}
      <div className="claims">{[['verified', 'Supporting claims recorded as verified'], ['rejected', 'Rejected claims — not supporting evidence']].map(([status, heading]) => <section key={status}><h3 className="evidence-group-title">{heading}</h3>{explanation.claims.some((claim) => claim.status === status) ? explanation.claims.filter((claim) => claim.status === status).map((claim) => <Claim key={claim.claim_id} claim={claim} />) : <p className="caption">None recorded.</p>}</section>)}</div>
      <div className="two-column mt-6"><TextList title="Counter-case" items={explanation.counter_case} /><TextList title="Ruled out" items={explanation.ruled_out} /></div>
      <div className="model-line"><span>Analyst: {explanation.models.analyst}</span><span>Skeptic: {explanation.models.skeptic}</span><span>Retries: {number(explanation.retries)}</span></div><p className="caption">Explanation ID: {explanation.explanation_id}</p>
    </> : <Empty title={row.explanation_id ? 'Explanation unavailable' : 'No explanation recorded'}>{row.explanation_id ? 'The referenced explanation is not present in this run.' : 'This instrument has a recorded ranking, but no analyst explanation was supplied.'}</Empty>}
  </section>;
}
export default function Detail() {
  const { pool, symbol } = useParams();
  const { data } = useRunOutput();
  const { isPro, marketPath } = usePresentation();
  const location = useLocation();
  const record = researchRecord(data, pool, symbol);
  if (!record) return <NotFound title="Instrument not found">This pool and symbol do not identify an instrument in the current run.</NotFound>;
  const { row, pool: poolSummary, explanation } = record;
  const back = safeMarketReturn(location.state?.from || marketPath, pool);
  const contributions = contributionsSorted(row);
  const factorTitle = (factor) => data.factor_cards.find((card) => card.pool === pool && card.factor === factor)?.title || factor;
  const sum = contributions.reduce((value, item) => value + item.contribution, 0);
  const chart = {
    grid: { left: 10, right: 55, top: 12, bottom: 45, containLabel: true },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText', valueFormatter: formatScore },
    xAxis: { type: 'value', name: 'Score contribution', nameLocation: 'middle', nameGap: 30 },
    yAxis: { type: 'category', inverse: true, data: contributions.map((item) => factorTitle(item.factor)), axisLabel: { width: 115, overflow: 'truncate' } },
    series: [{ type: 'bar', barMaxWidth: 25, label: { show: true, position: 'right', formatter: (info) => formatScore(info.value), fontSize: 13 }, data: contributions.map((item) => ({ value: item.contribution, itemStyle: { color: item.contribution < 0 ? '#954b26' : '#0b7068' } })) }],
  };
  const metrics = <Metrics items={[["Pool rank", `${number(row.rank)} of ${number(data.recommendations.filter((item) => item.pool === pool).length)}`], ['Composite score', formatScore(row.score)], ['Expected alpha', formatBps(row.expected_alpha_bps)], ['Net edge', formatBps(row.net_edge_bps)], ['Round-trip cost', formatBps(row.cost_bps_round_trip)], ['Coverage', formatPct(row.coverage)], ['Horizon', `${number(row.horizon_days)} days`], ['Pool composite IC', formatScore(poolSummary?.composite_ic)]]} />;
  const contributionPanel = <section className="card" key="contributions" id="measurements" tabIndex={-1} aria-labelledby="contribution-title">
    <div className="section-heading"><div><p className="eyebrow">Original measurements / Score decomposition</p><h2 id="contribution-title">What drives this score?</h2></div><Link to={`/factors?pool=${pool}`} className="text-link">Explore Factor Lab ↗</Link></div>
    <p className="section-description">A signed contribution shows how a recorded factor enters the score. A negative contribution does not prove a negative future return. Coverage describes available data, not confidence.</p>
    {contributions.length ? <Chart option={chart} height={Math.max(250, contributions.length * 48 + 70)} label="Factor contributions ordered by absolute magnitude. Positive and negative signed values contribute to the composite score." /> : <Empty>No contributions are supplied.</Empty>}
    <p className="caption">Contributions sum to the score. Recorded sum: {formatScore(sum)} · Score: {formatScore(row.score)}. Positive = teal; negative = amber; each value carries its sign.</p>
    {Math.abs(sum - row.score) > 0.0001 && <p className="notice">The recorded contribution sum differs from the score. Source values are preserved.</p>}
    <details className="research-details"><summary>View contribution measurements</summary><TableScroll label="Underlying contribution values"><table><thead><tr><th scope="col">Factor</th><th scope="col">Z-score</th><th scope="col">Weight</th><th scope="col">Contribution</th></tr></thead><tbody>{contributions.map((item) => <tr key={item.factor}><th scope="row">{factorTitle(item.factor)}<small className="block muted">{item.factor}</small></th><td>{formatScore(item.z)}</td><td>{formatPct(item.weight)}</td><td>{formatScore(item.contribution)}</td></tr>)}</tbody></table></TableScroll></details>
    <details className="research-details" open={isPro}><summary>All original instrument metrics</summary>{metrics}<p className="caption">Expected alpha and net edge are estimates in basis points, not realized returns. Score is unitless. Rank is within this pool.</p></details>
  </section>;
  const explanationPanel = <ExplanationPanel key="explanation" explanation={explanation} row={row} />;
  const risks = <section className="card" id="risks" tabIndex={-1} key="risks" aria-labelledby="risk-title"><div className="section-heading"><div><p className="eyebrow">Limits of the research</p><h2 id="risk-title">What could invalidate this stance?</h2></div></div><div className="two-column"><TextList title="Invalidation conditions" items={row.invalidation} /><TextList title="What to watch" items={row.what_to_watch} /></div><p className="caption">These are the conditions recorded by the source. They are not a complete assessment of suitability or investment risk. {data.data_mode === 'SYNTHETIC' ? 'This is a fictional instrument with generated research records.' : 'Inspect the original source and its timing before drawing a conclusion.'}</p></section>;
  return <>
    <Link className="text-link" to={back}>← Back to {poolSummary?.label || 'leaderboard'}</Link>
    <PageTitle eyebrow={`${poolSummary?.label || pool} / ${row.sector}`} title={row.symbol} action={<div className="flex flex-wrap gap-2"><Tier value={row.tier} />{row.regime_adjusted && <Badge tone="elevated">Adjusted by regime</Badge>}</div>}><p>{row.name}</p></PageTitle>
    <section className="card detail-overview"><h2>What is the recorded research stance?</h2><StanceMeaning tier={row.tier} /><div className="detail-context"><span>Pool: {poolSummary?.label || row.pool}</span><span>Source tier: {row.tier}</span><span>As of {data.as_of}</span><span>Horizon: {number(row.horizon_days)} days</span><span>Data mode: {data.data_mode}</span></div><p className="caption">Run created: {data.created_at}. The decision date is the data context, not a claim of current market freshness.</p></section>
    {row.tier === 'NO_CALL' && <div className="notice">No call — the source run records no directional research stance. No specific reason code is supplied for this instrument. Inspect coverage, pool IC and the available explanation; no stance has been inferred.</div>}
    {isPro ? metrics : <Metrics items={[["Pool rank", `${number(row.rank)} of ${number(data.recommendations.filter((item) => item.pool === pool).length)}`], ['Composite score', formatScore(row.score)]]} />}
    <nav className="detail-sections" aria-label="Instrument research sections"><a className="text-link" href="#explanation">Evidence and counter-case ↓</a><a className="text-link" href="#risks">Risks and invalidation ↓</a><a className="text-link" href="#measurements">Original measurements ↓</a></nav>
    {isPro ? [contributionPanel, explanationPanel, risks] : [explanationPanel, risks, contributionPanel]}
    <div className="hero-actions"><Link className="button" to="/trace">Inspect run trace →</Link><Link className="text-link" to="/discover">Return to Discover</Link></div>
  </>;
}
