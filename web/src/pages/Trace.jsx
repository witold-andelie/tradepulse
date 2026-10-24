import { ViewIntro } from '../components/ResearchGuide.jsx';
import { usePresentation } from '../hooks/usePresentation.jsx';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { loadValidatedTrace as loadTrace } from '../api/client.js';
import { useRunOutput } from '../hooks/useRunOutput.jsx';
import { dataModeBanner } from '../lib/data.js';
import { summarizeTrace } from '../lib/trace.js';
import { Badge, Empty, ErrorState, Loading, Metrics, number, PageTitle, TableScroll, tickerPath } from '../components/ui.jsx';
import Chart from '../components/Chart.jsx';
export default function Trace({ events: suppliedEvents } = {}) {
  const { data } = useRunOutput();
  const [state, setState] = useState({ events: null, loading: true, error: null });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (suppliedEvents) {
      setState({ events: suppliedEvents, loading: false, error: null });
      return undefined;
    }
    const controller = new AbortController();
    let current = true;
    setState({ events: null, loading: true, error: null });
    loadTrace(data.run_id, { signal: controller.signal }).then((events) => { if (current) setState({ events, loading: false, error: null }); }, (error) => { if (current) setState({ events: null, loading: false, error }); });
    return () => { current = false; controller.abort(); };
  }, [data.run_id, attempt, suppliedEvents]);
  return <><PageTitle eyebrow="Observability / Decision provenance" title="Run Trace"><p>Inspect the recorded pipeline, verifier decisions and retries. A trace describes analysis; it does not establish trade execution.</p></PageTitle>{state.loading ? <Loading /> : state.error ? <ErrorState error={state.error} retry={() => setAttempt((value) => value + 1)} /> : <TraceContent events={state.events} data={data} />}</>;
}
function TraceContent({ events, data }) {
  const { isPro } = usePresentation();
  const [node, setNode] = useState('');
  const [kind, setKind] = useState('');
  const [timing, setTiming] = useState('reported');
  const summary = useMemo(() => summarizeTrace(events), [events]);
  const nodes = [...new Set(summary.ordered.map((event) => event.node))];
  const kinds = [...new Set(summary.ordered.map((event) => event.kind))];
  const filtered = summary.ordered.filter((event) => (!node || event.node === node) && (!kind || event.kind === kind));
  const mismatches = summary.pairs.filter((pair) => pair.reportedMs != null && pair.reportedMs !== pair.intervalMs);
  const modes = [...new Set(events.map((event) => event.data_mode))];
  const timelinePairs = summary.pairs.filter((pair) => (timing === 'reported' ? pair.reportedMs : pair.intervalMs) != null && pair.intervalMs >= 0);
  const timeline = { grid: { left: 10, right: 25, top: 30, bottom: 40, containLabel: true },
    xAxis: { type: 'value', name: 'Seconds from first event', nameLocation: 'middle', nameGap: 25 }, yAxis: { type: 'category', inverse: true, data: timelinePairs.map((pair) => `${pair.start.node} · ${number(pair.start.seq)}`), axisLabel: { fontSize: 10, width: 125, overflow: 'truncate' } },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText', formatter: (items) => { const pair = timelinePairs[items[0].dataIndex]; return `${pair.start.node}\nStart: ${pair.start.ts}\nEnd: ${pair.end.ts}\nTimestamp interval: ${number(pair.intervalMs)} ms\nReported duration: ${number(pair.reportedMs)} ms`; } },
    series: [{ name: 'Offset', type: 'bar', stack: 'time', silent: true, itemStyle: { color: 'transparent' }, emphasis: { disabled: true }, data: timelinePairs.map((pair) => (Date.parse(pair.start.ts) - summary.firstMs) / 1000) }, { name: timing === 'reported' ? 'Reported duration' : 'Timestamp interval', type: 'bar', stack: 'time', barMaxWidth: 22, barMinHeight: 2, data: timelinePairs.map((pair) => ({ value: (timing === 'reported' ? pair.reportedMs : pair.intervalMs) / 1000, itemStyle: { color: pair.end.status === 'error' ? '#b56c37' : '#166b65' } })) }],
  };
  if (!events.length) return <section className="card"><Empty title="No trace events recorded">The run has no trace records. No pipeline activity has been inferred.</Empty></section>;
  return <>{modes.filter((mode) => mode !== data.data_mode).map((mode) => { const banner = dataModeBanner(mode); return <div key={mode} className="notice">Trace provenance differs from run mode: {mode}. {banner.text}</div>; })}
    <ViewIntro><p>This is a record of analysis, not an Agent conversation or an execution log for trades. The summary below comes only from complete node pairs and actual retry/error events. Missing stages are not filled in.</p></ViewIntro>
    {!isPro && <section aria-labelledby="workflow-title"><div className="section-heading"><div><p className="eyebrow">What this trace actually records</p><h2 id="workflow-title">Recorded research workflow</h2></div></div><ol className="simple-trace-list">{summary.pairs.map((pair) => <li key={pair.start.seq}><h3>{pair.start.node.replaceAll('_', ' ')}</h3><p><Badge tone={pair.end.status === 'error' ? 'negative' : 'neutral'}>{pair.end.status}</Badge> Sequence {number(pair.start.seq)} → {number(pair.end.seq)}</p><p>{pair.end.message}</p><p>Timestamp interval: {number(pair.intervalMs)} ms. Reported duration: {number(pair.reportedMs)} ms.</p><p><code>{pair.start.ts}</code></p></li>)}</ol>{summary.ordered.filter((event) => event.kind === 'retry' || event.kind === 'error').map((event) => <p className="notice" key={event.seq}><strong>{event.kind} · {event.node} · sequence {number(event.seq)}</strong><br />{event.message}</p>)}</section>}
    <p className="caption">Run ID: {data.run_id} · Source: {data.trace_path} · Trace data mode: {modes.join(', ')}</p>
    <Metrics items={[["Timestamp span", `${number(summary.spanMs, 3)} ms`], ['Explicit LLM-call events', number(summary.llmCalls)], ['Reported tokens in', summary.tokenReports ? number(summary.tokensIn) : '—'], ['Reported tokens out', summary.tokenReports ? number(summary.tokensOut) : '—']]} />
    <p className="caption">Totals cover all events, independent of filters. Token totals sum reported event fields; no missing usage is inferred. LLM calls count only explicit llm_call events.</p>
    {mismatches.length > 0 && <p className="notice">Timing discrepancy: {number(mismatches.length)} paired node(s) have a reported duration that differs from their timestamp interval. The timeline defaults to reported durations anchored at recorded start times. Select timestamp intervals to compare; neither value is overwritten.</p>}
    {(summary.unmatchedStarts > 0 || summary.unmatchedEnds > 0) && <p className="notice">Unmatched boundaries: {number(summary.unmatchedStarts)} start(s), {number(summary.unmatchedEnds)} end(s). These events remain in the event list and cannot form complete timeline bars.</p>}
    <section className="card"><div className="section-heading"><div><p className="eyebrow">Recorded analysis stages</p><h2>Pipeline timeline</h2></div><label>Timing source<select aria-label="Timing source" value={timing} onChange={(event) => setTiming(event.target.value)}><option value="reported">Reported node duration</option><option value="timestamps">Paired timestamp interval</option></select></label></div>{timelinePairs.length ? <Chart label={`Pipeline timeline using ${timing === 'reported' ? 'reported durations' : 'timestamp intervals'}, with start offsets from the first trace event.`} option={timeline} height={Math.max(260, timelinePairs.length * 35 + 80)} /> : <Empty title="No complete timeline pairs" />}<p className="caption">Minimum visible bar width is two pixels; use the exact measurements below for very short intervals.</p><details className="research-details"><summary>Paired timing measurements</summary><TableScroll label="Exact paired node timing"><table><thead><tr><th scope="col">Node</th><th scope="col">Start</th><th scope="col">End</th><th scope="col">Timestamp interval (ms)</th><th scope="col">Reported duration (ms)</th></tr></thead><tbody>{summary.pairs.map((pair) => <tr key={pair.start.seq}><td>{pair.start.node}</td><td>{pair.start.ts}</td><td>{pair.end.ts}</td><td>{number(pair.intervalMs)}</td><td>{number(pair.reportedMs)}</td></tr>)}</tbody></table></TableScroll></details></section>
    <details className="trace-event-disclosure" open={isPro}><summary>Inspect full event chronology and filters</summary>
    <section className="card table-card"><div className="section-heading"><div><p className="eyebrow">Evidence and intermediate decisions</p><h2>Event log</h2></div><span className="result-count" aria-live="polite">{number(filtered.length)} of {number(events.length)} events</span></div><div className="filter-bar pb-5"><label>Pipeline node<select aria-label="Pipeline node" value={node} onChange={(event) => setNode(event.target.value)}><option value="">All nodes</option>{nodes.map((value) => <option key={value}>{value}</option>)}</select></label><label>Event kind<select aria-label="Event kind" value={kind} onChange={(event) => setKind(event.target.value)}><option value="">All kinds</option>{kinds.map((value) => <option key={value}>{value}</option>)}</select></label><button className="button" onClick={() => { setNode(''); setKind(''); }}>Clear filters</button></div>
    {filtered.length ? <TableScroll label="Decision trace event log"><table className="event-table"><thead><tr>{['Seq', 'Time (UTC)', 'Node', 'Kind', 'Status', 'Model', 'Tokens in / out', 'Message and payload'].map((label) => <th scope="col" key={label}>{label}</th>)}</tr></thead><tbody>{filtered.map((event) => { const row = data.recommendations.find((item) => item.pool === event.payload.pool && item.symbol === event.payload.symbol); return <tr key={event.seq} className={event.kind === 'error' || event.status === 'error' ? 'event-error' : event.kind === 'retry' ? 'event-retry' : ''}><td>{number(event.seq)}</td><td className="whitespace-nowrap">{event.ts}</td><td>{event.node}</td><td><Badge tone={event.kind === 'retry' ? 'elevated' : event.kind === 'error' ? 'negative' : 'muted'}>{event.kind === 'retry' ? '↻ ' : event.kind === 'error' ? '✗ ' : ''}{event.kind}</Badge></td><td>{event.status}</td><td>{event.model || '—'}</td><td>{number(event.tokens_in)} / {number(event.tokens_out)}</td><td><p>{event.message}</p><details className="event-payload"><summary>Inspect payload</summary><pre>{JSON.stringify(event.payload, null, 2)}</pre><p>Data mode: {event.data_mode} · Duration: {number(event.duration_ms)} ms</p>{row && <Link className="text-link" to={tickerPath(row)}>Instrument: {row.symbol} ↗</Link>}</details></td></tr>; })}</tbody></table></TableScroll> : <Empty title="No trace events match these filters" action={<button className="button" onClick={() => { setNode(''); setKind(''); }}>Reset event filters</button>} />}</section></details></>;
}
