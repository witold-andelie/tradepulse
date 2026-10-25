import { SourceText } from '../i18n/Locale.jsx';
import { poolName, enumName, factorName, indicatorName } from '../i18n/labels.js';
import { useLocale, Message } from "../i18n/Locale.jsx";
import { ViewIntro } from '../components/ResearchGuide.jsx';
import { useSearchParams } from 'react-router-dom';
import { useRunOutput } from '../hooks/useRunOutput.jsx';
import { formatPct, formatScore } from '../lib/format.js';
import { Badge, Empty, Gate, number, PageTitle, TableScroll } from '../components/ui.jsx';
import Chart from '../components/Chart.jsx';

export default function Factors({ factorCards } = {}) {
  const { t, locale } = useLocale();
  const { data: contextRun } = useRunOutput();
  const data = factorCards ? { ...contextRun, factor_cards: factorCards } : contextRun;
  const [params, setParams] = useSearchParams();
  const pool = params.get('pool') || data.pools[0]?.pool || '';
  const status = params.get('status') || '';
  const cards = data.factor_cards.filter((card) => card.pool === pool && (!status || card.status === status));
  const update = (key, value) => { const next = new URLSearchParams(params); value ? next.set(key, value) : next.delete(key); setParams(next, { replace: true }); };
  return <><PageTitle eyebrow={t("Research / Factor diagnostics")} title={t("Factor Lab")}><p>{t("Measure ≠ predict ≠ earn.")}</p></PageTitle>
    <ViewIntro><p>{t("A factor can measure a pattern without predicting a later move, and an apparent prediction can lose its edge after costs. Read each gate separately. A failed or unevaluated gate is a limitation, not a positive recommendation.")}</p></ViewIntro>
    <details className="card gate-explainer"><summary>{t("How do the five research gates work?")}</summary><ol className="text-list"><li><Message text="{value1} checks the definition and data coverage." values={{value1: <strong>{t("G1 · Measure:")}</strong>}} /></li><li><Message text="{value1} asks whether a factor adds information beyond the baseline." values={{value1: <strong>{t("G2 · Incremental:")}</strong>}} /></li><li><Message text="{value1} evaluates the lagged predictive signal, separately from same-day description." values={{value1: <strong>{t("G3 · Predictive:")}</strong>}} /></li><li><Message text="{value1} evaluates the long-short signal after modeled costs." values={{value1: <strong>{t("G4 · Net of cost:")}</strong>}} /></li><li><Message text="{value1} checks whether the IC sign agrees across window halves." values={{value1: <strong>{t("G5 · Consistency:")}</strong>}} /></li></ol><p className="caption">{t("Methodology: docs/architecture/factors.md. The recorded gate outcomes and measurements below are preserved unchanged.")}</p></details>
    <div className="card principle"><p className="eyebrow">{t("Explanatory text · Factor and gate specification")}</p><p>{t("A signal can describe today's market well and still predict nothing. A factor can predict and still lose its edge to costs. A strategy can make money for a reason other than the one in its name.")}</p><p className="caption">{t("Source: docs/architecture/factors.md. These controls provide exploratory visualization of recorded factor cards. They do not recompute the model.")}</p></div>
    <div className="page-controls"><label><Message text="Asset pool{value1}" values={{value1: <select aria-label={t("Asset pool")} value={pool} onChange={(event) => update('pool', event.target.value)}>{data.pools.map((item) => <option key={item.pool} value={item.pool}>{poolName(item.pool, t, item.label)}</option>)}</select>}} /></label><label><Message text="Factor status{value1}" values={{value1: <select aria-label={t("Factor status")} value={status} onChange={(event) => update('status', event.target.value)}><option value="">{t("All statuses")}</option>{['ACTIVE', 'MEASURED_ONLY', 'INSUFFICIENT_DATA'].map((value) => <option key={value} value={value}>{enumName(value, t)}</option>)}</select>}} /></label><span className="muted text-xs" aria-live="polite"><Message text="{value1} recorded factors" values={{value1: number(cards.length)}} /></span></div>
    {data.data_mode === 'SYNTHETIC' && <p className="notice">{t("Synthetic gate outcomes and measurements are generated independently. Reported outcomes are displayed as supplied, even when a value and threshold appear inconsistent.")}</p>}
    {cards.length ? <div className="factor-grid">{cards.map((card) => <FactorCard key={`${card.pool}-${card.factor}`} card={card} />)}</div> : <section className="card"><Empty title={t("No factor cards match this selection")} action={<button className="button" onClick={() => setParams({ pool: data.pools[0]?.pool || '' })}>{t("Reset selection")}</button>}>{t("No compatible research records were supplied for this pool and status.")}</Empty></section>}</>;
}
function FactorCard({ card }) {
  const { t, locale } = useLocale();
  const validDecay = card.ic_decay.some((item) => item.mean_ic != null);
  const option = {
    grid: { left: 12, right: 15, top: 35, bottom: 35, containLabel: true },
    xAxis: { type: 'category', data: card.ic_decay.map((item) => `${number(item.horizon_days)}d`), name: t("Horizon"), nameLocation: 'middle', nameGap: 23 },
    yAxis: { type: 'value', name: t("Mean rank IC"), nameTextStyle: { fontSize: 10, align: 'left' }, axisLabel: { fontSize: 10 } },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText', formatter: (items) => { const item = card.ic_decay[items[0].dataIndex]; return t("Horizon: {value1}d\nMean IC: {value2}\nt-stat: {value3}\nn: {value4}", {value1: number(item.horizon_days), value2: formatScore(item.mean_ic), value3: number(item.t_stat, 3), value4: number(item.n)}); } },
    series: [{ type: 'bar', barMaxWidth: 42, data: card.ic_decay.map((item) => ({ value: item.mean_ic, itemStyle: { color: item.mean_ic < 0 ? '#bd6c36' : '#166b65' } })) }],
  };
  return <article className="card factor-card"><div className="section-heading"><div><h2>{factorName(card.factor, t, card.title)}</h2><p className="caption font-mono">{card.factor}</p></div><Badge tone={card.status}>{card.status}</Badge></div><p className="text-sm muted leading-6"><SourceText inline>{card.measures}</SourceText></p>
    <dl className="factor-metrics"><div><dt>{t("Model weight")}</dt><dd><bdi dir="ltr">{formatPct(card.weight)}</bdi></dd></div><div><dt>{t("Coverage")}</dt><dd><bdi dir="ltr">{formatPct(card.coverage)}</bdi></dd></div><div><dt>{t("Same-day IC")}</dt><dd><bdi dir="ltr">{formatScore(card.same_day_ic)}</bdi></dd></div></dl>
    <div className="gate-grid" aria-label={t("Five factor gates")}>{card.gates.map((gate) => <div className="gate-chip" key={gate.gate}><div><strong>{gate.gate}</strong><span>{indicatorName(gate.name, t)}</span></div><Gate value={gate.passed} /><small><Message text="Value {value1} / threshold {value2}" values={{value1: number(gate.value, 4), value2: number(gate.threshold, 4)}} /></small><small><SourceText inline>{gate.note}</SourceText></small></div>)}</div>
    {card.mostly_descriptive && <p className="notice">{t("Mostly descriptive — same-day IC is stronger than the lagged predictive signal.")}</p>}
    <h3 className="mt-5">{t("IC decay")}</h3>{validDecay ? <Chart label={t("Mean rank IC across recorded horizons for {value1}", {value1: factorName(card.factor, t, card.title)})} option={option} height={205} /> : <div className="small-empty">{t("IC decay unavailable — no measured observations.")}</div>}
    <TableScroll label={t("Recorded IC observations for {value1}", {value1: factorName(card.factor, t, card.title)})}><table className="compact-table"><thead><tr><th scope="col">{t("Horizon (days)")}</th><th scope="col">{t("Mean IC")}</th><th scope="col">{t("t-stat")}</th><th scope="col">n</th></tr></thead><tbody>{card.ic_decay.map((item) => <tr key={item.horizon_days}><td><bdi dir="ltr">{number(item.horizon_days)}</bdi></td><td><bdi dir="ltr">{formatScore(item.mean_ic)}</bdi></td><td><bdi dir="ltr">{number(item.t_stat, 3)}</bdi></td><td><bdi dir="ltr">{number(item.n)}</bdi></td></tr>)}</tbody></table></TableScroll>
    <details className="research-details" open><summary>{t("Long-short research measurements")}</summary><dl className="key-values"><dt>{t("Gross annual return")}</dt><dd><bdi dir="ltr">{formatPct(card.long_short.gross_ann_return)}</bdi></dd><dt>{t("Net annual return")}</dt><dd><bdi dir="ltr">{formatPct(card.long_short.net_ann_return)}</bdi></dd><dt>{t("Net Sharpe")}</dt><dd><bdi dir="ltr">{number(card.long_short.net_sharpe, 3)}</bdi></dd><dt>{t("Turnover per rebalance")}</dt><dd><bdi dir="ltr">{formatPct(card.long_short.turnover_per_rebalance)}</bdi></dd><dt>{t("Max drawdown")}</dt><dd><bdi dir="ltr">{formatPct(card.long_short.max_drawdown)}</bdi></dd></dl></details>
    <details className="research-details"><summary>{t("Definition and availability")}</summary><dl className="key-values"><dt>{t("Definition")}</dt><dd><SourceText>{card.definition}</SourceText></dd><dt>{t("Sources")}</dt><dd>{card.sources.join(', ') || t("None recorded")}</dd><dt>{t("Available")}</dt><dd><SourceText>{card.availability}</SourceText></dd></dl></details>
    <p className="caption research-window"><Message text="In-sample research window: {value1} – {value2}. Research diagnostics, not realized trading performance." values={{value1: card.window.start, value2: card.window.end}} /></p></article>;
}
