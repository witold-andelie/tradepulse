import { useMemo } from 'react';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { flexRender, getCoreRowModel, getPaginationRowModel, useReactTable } from '@tanstack/react-table';
import { useRunOutput } from '../hooks/useRunOutput.jsx';
import { filterRecommendations, sectorSummary, sortRecommendations } from '../lib/data.js';
import { formatBps, formatPct, formatScore } from '../lib/format.js';
import { TIER_ORDER, tierLabel } from '../lib/tiers.js';
import { Badge, Empty, Metrics, NotFound, number, PageTitle, TableScroll, tickerPath, Tier } from '../components/ui.jsx';
import Chart from '../components/Chart.jsx';
import MeasurementDisclosure from '../components/MeasurementDisclosure.jsx';
import CandidateCard from '../components/CandidateCard.jsx';
import { ViewIntro } from '../components/ResearchGuide.jsx';
import { usePresentation } from '../hooks/usePresentation.jsx';

export default function Leaderboard({ run, pool: selectedPool } = {}) {
  const { pool: routePool } = useParams();
  const { data: contextRun } = useRunOutput();
  const data = run || contextRun;
  const pool = selectedPool || routePool;
  const summary = data.pools.find((item) => item.pool === pool);
  if (!summary) return <NotFound title="Asset pool not found" />;
  return <PoolBoard key={pool} data={data} summary={summary} />;
}
function PoolBoard({ data, summary }) {
  const pool = summary.pool;
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.pathname + location.search;
  const { isPro } = usePresentation();
  const [params, setParams] = useSearchParams();
  const query = params.get('q') || '';
  const sector = params.get('sector') || '';
  const tiers = params.getAll('tier');
  const sortKey = params.get('sort') || 'rank';
  const sortDir = params.get('dir') === 'desc' ? 'desc' : 'asc';
  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => { next.delete(key); (Array.isArray(value) ? value : [value]).filter(Boolean).forEach((item) => next.append(key, item)); });
    next.delete('page');
    setParams(next, { replace: true, flushSync: true });
  };
  const rows = useMemo(() => filterRecommendations(data.recommendations, { pool }), [data, pool]);
  const sectors = useMemo(() => sectorSummary(rows), [rows]);
  const filtered = useMemo(() => filterRecommendations(rows, { query, sector, tiers }), [rows, query, sector, tiers.join('|')]);
  const sorted = useMemo(() => sortRecommendations(filtered, sortKey, sortDir), [filtered, sortKey, sortDir]);
  const extremes = useMemo(() => sortRecommendations(rows, 'rank'), [rows]);
  const requestedPage = Number(params.get('page') || 1);
  const pagination = { pageIndex: Math.min(Math.max(0, Number.isInteger(requestedPage) ? requestedPage - 1 : 0), Math.max(0, Math.ceil(sorted.length / 50) - 1)), pageSize: 50 };
  const setPagination = (change) => {
    const nextPage = typeof change === 'function' ? change(pagination) : change;
    const next = new URLSearchParams(params);
    nextPage.pageIndex ? next.set('page', String(nextPage.pageIndex + 1)) : next.delete('page');
    setParams(next, { replace: true, flushSync: true });
  };
  const columns = useMemo(() => [
    ['rank', 'Rank', number], ['symbol', 'Instrument', (value, row) => <Link className="symbol" to={tickerPath(row)} state={{ from }}>{value}<span className="instrument-name">{row.name}</span></Link>],
    ['name', 'Name'], ['sector', 'Sector'], ['tier', 'Research stance', (value) => <Tier value={value} />], ['score', 'Score', formatScore],
    ['net_edge_bps', 'Net edge (bp)', formatBps], ['expected_alpha_bps', 'Expected α (bp)', formatBps], ['coverage', 'Coverage', formatPct], ['ret_1d', '1-day return', formatPct],
  ].map(([key, label, format]) => ({ id: key, accessorKey: key, header: label, enableSorting: !['tier', 'sector'].includes(key), cell: ({ getValue, row }) => format ? key === 'symbol' ? format(getValue(), row.original) : format(getValue()) : getValue() })), [from]);
  const table = useReactTable({ data: sorted, columns, getCoreRowModel: getCoreRowModel(), getPaginationRowModel: getPaginationRowModel(), state: { pagination, columnVisibility: { name: false } }, onPaginationChange: setPagination, manualSorting: true, autoResetPageIndex: false });
  const limit = Math.max(0.01, ...sectors.map((item) => Math.abs(item.meanScore)));
  const treemap = {
    tooltip: { trigger: 'item', confine: true, renderMode: 'richText', formatter: (info) => `${info.name}\nInstruments: ${number(info.value[0])}\nMean score: ${formatScore(info.value[1])}` },
    visualMap: { type: 'continuous', min: -limit, max: limit, dimension: 1, seriesIndex: 0, orient: 'horizontal', left: 'center', bottom: 0, calculable: false, text: ['Higher mean score', 'Lower'], inRange: { color: ['#f4d8c6', '#f2f3fb', '#c4e6dd'] } },
    series: [{ type: 'treemap', top: 0, bottom: 58, left: 0, right: 0, roam: false, nodeClick: false, breadcrumb: { show: false }, label: { show: true, color: '#132b33', overflow: 'truncate', formatter: (info) => `${info.name}\n${formatScore(info.value[1])}` }, itemStyle: { borderWidth: 1, borderColor: '#6b7890', gapWidth: 3 }, data: sectors.map((item) => ({ name: item.sector, value: [item.count, item.meanScore] })) }],
  };
  return <><PageTitle eyebrow="Universe / Recommendation leaderboard" title={summary.label} action={<Badge tone={summary.regime_state}>{summary.regime_state} regime</Badge>}><p>Explore ranked instruments. Follow the evidence behind each research stance.</p></PageTitle>
    <ViewIntro><p>Start with an instrument, then follow “Why this stance?” to inspect the recorded explanation and its counterevidence. Rankings are relative to this pool. Coverage is data availability, not confidence.</p></ViewIntro>
    <Metrics items={[["Loaded instruments", number(rows.length)], ['Ranked / members (reported)', `${number(summary.n_ranked)} / ${number(summary.n_members)}`], ['Composite rank IC', formatScore(summary.composite_ic)], ['Benchmark', summary.benchmark]]} />
    {isPro && <div className="overview-grid"><section className="card"><div className="section-heading"><div><p className="eyebrow">Cross-sectional view</p><h2>Sector score map</h2></div><span className="muted text-xs">Click a sector to filter</span></div>{sectors.length ? <Chart label="Sector treemap. Block size is instrument count; color is mean composite score. The sector selector offers the same filter by keyboard." option={treemap} height={260} onEvents={{ click: (event) => update({ sector: event.name }) }} /> : <Empty>No sector records.</Empty>}<p className="caption">Area = instrument count · Color = mean score · Scores are unitless.</p><MeasurementDisclosure title="Sector values and keyboard filters"><TableScroll label="Sector summary and accessible filters"><table><thead><tr><th scope="col">Sector filter</th><th scope="col">Instruments</th><th scope="col">Mean score</th><th scope="col">Overweight stances</th><th scope="col">Underweight stances</th></tr></thead><tbody>{sectors.map((item) => <tr key={item.sector}><th scope="row"><button className="button" onClick={() => update({ sector: item.sector })}>{item.sector}</button></th><td>{number(item.count)}</td><td>{formatScore(item.meanScore)}</td><td>{number(item.overweight)}</td><td>{number(item.underweight)}</td></tr>)}</tbody></table></TableScroll></MeasurementDisclosure></section>
    <section className="card extremes"><div className="section-heading"><div><p className="eyebrow">Score extremes</p><h2>Research shortlist</h2></div><span className="muted text-xs">By pool rank</span></div><div className="shortlist-grid">{[['Top 5', extremes.slice(0, 5)], ['Bottom 5', extremes.slice(-5).reverse()]].map(([label, items]) => <div key={label}><h3>{label}</h3><ol>{items.map((row) => <li key={row.symbol}><Link to={tickerPath(row)} state={{ from }}><span className="symbol">{row.symbol}</span><span className={row.score < 0 ? 'negative' : 'positive'}>{formatScore(row.score)} <span aria-hidden="true">↗</span></span></Link></li>)}</ol></div>)}</div></section></div>}
    <section className="card table-card"><div className="section-heading"><div><p className="eyebrow">Instrument universe</p><h2>Recommendation leaderboard</h2></div><span className="result-count" aria-live="polite">{number(filtered.length)} of {number(rows.length)} instruments</span></div>
      <div className="filter-bar"><label className="search-field">Search instruments<input type="search" value={query} onChange={(event) => update({ q: event.target.value })} placeholder="Search symbol or name…" /></label><label>Sector<select aria-label="Sector" value={sector} onChange={(event) => update({ sector: event.target.value })}><option value="">All sectors</option>{sectors.map((item) => <option key={item.sector}>{item.sector}</option>)}</select></label><button className="button clear-button" onClick={() => { setParams({}, { replace: true, flushSync: true }); }}>Clear filters</button></div>
      {!isPro && <div className="simple-sort"><label>Sort candidates<select aria-label="Sort candidates" value={`${sortKey}:${sortDir}`} onChange={(event) => { const [sort, dir] = event.target.value.split(':'); update({ sort, dir }); }}>{[['rank', 'Rank'], ['score', 'Score'], ['net_edge_bps', 'Net edge'], ['expected_alpha_bps', 'Expected alpha'], ['coverage', 'Coverage'], ['ret_1d', '1-day return']].flatMap(([key, label]) => ['asc', 'desc'].map((dir) => <option key={`${key}:${dir}`} value={`${key}:${dir}`}>{label} · {dir === 'asc' ? 'Ascending' : 'Descending'}</option>))}</select></label></div>}
      <fieldset className="tier-filters"><legend>Research stance</legend>{TIER_ORDER.map((tier) => <label key={tier} className={tiers.includes(tier) ? 'checked' : ''}><input type="checkbox" checked={tiers.includes(tier)} onChange={() => update({ tier: tiers.includes(tier) ? tiers.filter((item) => item !== tier) : [...tiers, tier] })} />{tierLabel(tier)}</label>)}</fieldset>
      {filtered.length ? <>{isPro ? <TableScroll label="Sortable recommendation leaderboard"><table className="leaderboard"><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id} scope="col" aria-sort={sortKey === header.id ? sortDir === 'desc' ? 'descending' : 'ascending' : undefined}>{header.column.columnDef.enableSorting ? <button onClick={() => update({ sort: header.id, dir: sortKey === header.id && sortDir === 'asc' ? 'desc' : 'asc' })}>{header.column.columnDef.header}<span aria-hidden="true">{sortKey === header.id ? sortDir === 'asc' ? ' ↑' : ' ↓' : ' ↕'}</span></button> : header.column.columnDef.header}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.original.symbol} tabIndex={0} aria-label={`Open ${row.original.symbol} research`} onClick={(event) => { if (!event.target.closest('a')) navigate(tickerPath(row.original), { state: { from } }); }} onKeyDown={(event) => { if (event.key === 'Enter' && event.target === event.currentTarget) navigate(tickerPath(row.original), { state: { from } }); }}>{row.getVisibleCells().map((cell) => <td key={cell.id} className={['score', 'net_edge_bps', 'expected_alpha_bps'].includes(cell.column.id) ? cell.getValue() < 0 ? 'negative numeric' : 'positive numeric' : ''}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></TableScroll> : <div className="candidate-grid market-candidates">{table.getRowModel().rows.map((row) => <CandidateCard key={row.original.symbol} row={row.original} run={data} from={from} />)}</div>}
      <div className="pagination"><span>Showing {number(pagination.pageIndex * pagination.pageSize + 1)}–{number(Math.min((pagination.pageIndex + 1) * pagination.pageSize, filtered.length))} of {number(filtered.length)}</span><div><button className="button" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()}>← Previous</button><span>Page {number(pagination.pageIndex + 1)} of {number(table.getPageCount())}</span><button className="button" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>Next →</button></div></div></> : <Empty title="No instruments match your filters" action={<button className="button" onClick={() => setParams({})}>Clear all filters</button>}>Try another symbol, sector or research stance.</Empty>}
    </section></>;
}
