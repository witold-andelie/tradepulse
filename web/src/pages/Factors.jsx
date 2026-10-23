import { ViewIntro } from '../components/ResearchGuide.jsx';
import { useSearchParams } from 'react-router-dom';
import { useRunOutput } from '../hooks/useRunOutput.jsx';
import { formatPct, formatScore } from '../lib/format.js';
import { Badge, Empty, Gate, number, PageTitle, TableScroll } from '../components/ui.jsx';
import Chart from '../components/Chart.jsx';

export default function Factors() {
  const { data } = useRunOutput();
  const [params, setParams] = useSearchParams();
  const pool = params.get('pool') || data.pools[0]?.pool || '';
  const status = params.get('status') || '';
  const cards = data.factor_cards.filter((card) => card.pool === pool && (!status || card.status === status));
  const update = (key, value) => { const next = new URLSearchParams(params); value ? next.set(key, value) : next.delete(key); setParams(next, { replace: true }); };
  return <><PageTitle eyebrow="Research / Factor diagnostics" title="Factor Lab"><p>Measure ≠ predict ≠ earn.</p></PageTitle>
    <ViewIntro><p>A factor can measure a pattern without predicting a later move, and an apparent prediction can lose its edge after costs. Read each gate separately. A failed or unevaluated gate is a limitation, not a positive recommendation.</p></ViewIntro>
    <details className="card gate-explainer"><summary>How do the five research gates work?</summary><ol className="text-list"><li><strong>G1 · Measure:</strong> checks the definition and data coverage.</li><li><strong>G2 · Incremental:</strong> asks whether a factor adds information beyond the baseline.</li><li><strong>G3 · Predictive:</strong> evaluates the lagged predictive signal, separately from same-day description.</li><li><strong>G4 · Net of cost:</strong> evaluates the long-short signal after modeled costs.</li><li><strong>G5 · Consistency:</strong> checks whether the IC sign agrees across window halves.</li></ol><p className="caption">Methodology: docs/architecture/factors.md. The recorded gate outcomes and measurements below are preserved unchanged.</p></details>
    <div className="card principle"><p className="eyebrow">Explanatory text · Factor and gate specification</p><p>A signal can describe today's market well and still predict nothing. A factor can predict and still lose its edge to costs. A strategy can make money for a reason other than the one in its name.</p><p className="caption">Source: docs/architecture/factors.md. These controls provide exploratory visualization of recorded factor cards. They do not recompute the model.</p></div>
    <div className="page-controls"><label>Asset pool<select aria-label="Asset pool" value={pool} onChange={(event) => update('pool', event.target.value)}>{data.pools.map((item) => <option key={item.pool} value={item.pool}>{item.label}</option>)}</select></label><label>Factor status<select aria-label="Factor status" value={status} onChange={(event) => update('status', event.target.value)}><option value="">All statuses</option>{['ACTIVE', 'MEASURED_ONLY', 'INSUFFICIENT_DATA'].map((value) => <option key={value}>{value}</option>)}</select></label><span className="muted text-xs" aria-live="polite">{number(cards.length)} recorded factors</span></div>
    {data.data_mode === 'SYNTHETIC' && <p className="notice">Synthetic gate outcomes and measurements are generated independently. Reported outcomes are displayed as supplied, even when a value and threshold appear inconsistent.</p>}
    {cards.length ? <div className="factor-grid">{cards.map((card) => <FactorCard key={`${card.pool}-${card.factor}`} card={card} />)}</div> : <section className="card"><Empty title="No factor cards match this selection" action={<button className="button" onClick={() => setParams({ pool: data.pools[0]?.pool || '' })}>Reset selection</button>}>No compatible research records were supplied for this pool and status.</Empty></section>}</>;
}
function FactorCard({ card }) {
  const validDecay = card.ic_decay.some((item) => item.mean_ic != null);
  const option = {
    grid: { left: 12, right: 15, top: 35, bottom: 35, containLabel: true },
    xAxis: { type: 'category', data: card.ic_decay.map((item) => `${number(item.horizon_days)}d`), name: 'Horizon', nameLocation: 'middle', nameGap: 23 },
    yAxis: { type: 'value', name: 'Mean rank IC', nameTextStyle: { fontSize: 10, align: 'left' }, axisLabel: { fontSize: 10 } },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText', formatter: (items) => { const item = card.ic_decay[items[0].dataIndex]; return `Horizon: ${number(item.horizon_days)}d\nMean IC: ${formatScore(item.mean_ic)}\nt-stat: ${number(item.t_stat, 3)}\nn: ${number(item.n)}`; } },
    series: [{ type: 'bar', barMaxWidth: 42, data: card.ic_decay.map((item) => ({ value: item.mean_ic, itemStyle: { color: item.mean_ic < 0 ? '#bd6c36' : '#166b65' } })) }],
  };
  return <article className="card factor-card"><div className="section-heading"><div><h2>{card.title}</h2><p className="caption font-mono">{card.factor}</p></div><Badge tone={card.status}>{card.status}</Badge></div><p className="text-sm muted leading-6">{card.measures}</p>
    <dl className="factor-metrics"><div><dt>Model weight</dt><dd>{formatPct(card.weight)}</dd></div><div><dt>Coverage</dt><dd>{formatPct(card.coverage)}</dd></div><div><dt>Same-day IC</dt><dd>{formatScore(card.same_day_ic)}</dd></div></dl>
    <div className="gate-grid" aria-label="Five factor gates">{card.gates.map((gate) => <div className="gate-chip" key={gate.gate}><div><strong>{gate.gate}</strong><span>{gate.name.replaceAll('_', ' ')}</span></div><Gate value={gate.passed} /><small>Value {number(gate.value, 4)} / threshold {number(gate.threshold, 4)}</small><small>{gate.note}</small></div>)}</div>
    {card.mostly_descriptive && <p className="notice">Mostly descriptive — same-day IC is stronger than the lagged predictive signal.</p>}
    <h3 className="mt-5">IC decay</h3>{validDecay ? <Chart label={`Mean rank IC across recorded horizons for ${card.title}`} option={option} height={205} /> : <div className="small-empty">IC decay unavailable — no measured observations.</div>}
    <TableScroll label={`Recorded IC observations for ${card.title}`}><table className="compact-table"><thead><tr><th scope="col">Horizon (days)</th><th scope="col">Mean IC</th><th scope="col">t-stat</th><th scope="col">n</th></tr></thead><tbody>{card.ic_decay.map((item) => <tr key={item.horizon_days}><td>{number(item.horizon_days)}</td><td>{formatScore(item.mean_ic)}</td><td>{number(item.t_stat, 3)}</td><td>{number(item.n)}</td></tr>)}</tbody></table></TableScroll>
    <details className="research-details" open><summary>Long-short research measurements</summary><dl className="key-values"><dt>Gross annual return</dt><dd>{formatPct(card.long_short.gross_ann_return)}</dd><dt>Net annual return</dt><dd>{formatPct(card.long_short.net_ann_return)}</dd><dt>Net Sharpe</dt><dd>{number(card.long_short.net_sharpe, 3)}</dd><dt>Turnover per rebalance</dt><dd>{formatPct(card.long_short.turnover_per_rebalance)}</dd><dt>Max drawdown</dt><dd>{formatPct(card.long_short.max_drawdown)}</dd></dl></details>
    <details className="research-details"><summary>Definition and availability</summary><dl className="key-values"><dt>Definition</dt><dd>{card.definition}</dd><dt>Sources</dt><dd>{card.sources.join(', ') || 'None recorded'}</dd><dt>Available</dt><dd>{card.availability}</dd></dl></details>
    <p className="caption research-window">In-sample research window: {card.window.start} – {card.window.end}. Research diagnostics, not realized trading performance.</p></article>;
}
