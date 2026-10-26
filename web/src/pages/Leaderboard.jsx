import { poolName, sectorName, enumName } from '../i18n/labels.js';
import { Canonical, useLocale, Message } from "../i18n/Locale.jsx";
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
  const { t, locale } = useLocale();
  const { pool: routePool } = useParams();
  const { data: contextRun } = useRunOutput();
  const data = run || contextRun;
  const pool = selectedPool || routePool;
  const summary = data.pools.find((item) => item.pool === pool);
  if (!summary) return <NotFound title={t("Asset pool not found")} />;
  return <PoolBoard key={pool} data={data} summary={summary} />;
}
function PoolBoard({ data, summary }) {
  const { t, locale } = useLocale();
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
    ['rank', t("Rank"), number], ['symbol', t("Instrument"), (value, row) => <Link className="symbol" to={tickerPath(row)} state={{ from }}>{value}<span className="instrument-name">{row.name}</span></Link>],
    ['name', t("Name")], ['sector', t("Sector"), (value) => sectorName(value, t)], ['tier', t("Research stance"), (value) => <Tier value={value} />], ['score', t("Score"), formatScore],
    ['net_edge_bps', t("Net edge (bp)"), formatBps], ['expected_alpha_bps', t("Expected α (bp)"), formatBps], ['coverage', t("Coverage"), formatPct], ['ret_1d', t("1-day return"), formatPct],
  ].map(([key, label, format]) => ({ id: key, accessorKey: key, header: label, enableSorting: !['tier', 'sector'].includes(key), cell: ({ getValue, row }) => format ? key === 'symbol' ? format(getValue(), row.original) : format(getValue()) : getValue() })), [from, t]);
  const table = useReactTable({ data: sorted, columns, getCoreRowModel: getCoreRowModel(), getPaginationRowModel: getPaginationRowModel(), state: { pagination, columnVisibility: { name: false } }, onPaginationChange: setPagination, manualSorting: true, autoResetPageIndex: false });
  const limit = Math.max(0.01, ...sectors.map((item) => Math.abs(item.meanScore)));
  const treemap = {
    tooltip: { trigger: 'item', confine: true, renderMode: 'richText', formatter: (info) => t("{value1}\nInstruments: {value2}\nMean score: {value3}", {value1: sectorName(info.name, t), value2: number(info.value[0]), value3: formatScore(info.value[1])}) },
    visualMap: { type: 'continuous', min: -limit, max: limit, dimension: 1, seriesIndex: 0, orient: 'horizontal', left: 'center', bottom: 0, calculable: false, text: [(locale === 'en' ? t('Higher mean score') : t('Higher')), t('Lower')], itemHeight: 65, inRange: { color: ['#f4d8c6', '#f2f3fb', '#c4e6dd'] } },
    series: [{ type: 'treemap', top: 0, bottom: 58, left: 0, right: 0, roam: false, nodeClick: false, breadcrumb: { show: false }, label: { show: true, color: '#132b33', overflow: 'truncate', formatter: (info) => `${sectorName(info.name, t)}\n${formatScore(info.value[1])}` }, itemStyle: { borderWidth: 1, borderColor: '#6b7890', gapWidth: 3 }, data: sectors.map((item) => ({ name: item.sector, value: [item.count, item.meanScore] })) }],
  };
  return <><PageTitle eyebrow={t("Universe / Recommendation leaderboard")} title={poolName(summary.pool, t, summary.label)} action={<Badge tone={summary.regime_state}><Message text="{state} regime" values={{state: enumName(summary.regime_state, t)}} /></Badge>}><p>{t("Explore ranked instruments. Follow the evidence behind each research stance.")}</p></PageTitle>
    <ViewIntro><p>{t("Start with an instrument, then follow “Why this stance?” to inspect the recorded explanation and its counterevidence. Rankings are relative to this pool. Coverage is data availability, not confidence.")}</p></ViewIntro>
    <Metrics items={[[t("Loaded instruments"), number(rows.length)], [t("Ranked / members (reported)"), `${number(summary.n_ranked)} / ${number(summary.n_members)}`], [t("Composite rank IC"), formatScore(summary.composite_ic)], [t("Benchmark"), summary.benchmark]]} />
    {isPro && <div className="overview-grid"><section className="card"><div className="section-heading"><div><p className="eyebrow">{t("Cross-sectional view")}</p><h2>{t("Sector score map")}</h2></div><span className="muted text-xs">{t("Click a sector to filter")}</span></div>{sectors.length ? <Chart label={t("Sector treemap. Block size is instrument count; color is mean composite score. The sector selector offers the same filter by keyboard.")} option={treemap} height={260} onEvents={{ click: (event) => update({ sector: event.name }) }} /> : <Empty>{t("No sector records.")}</Empty>}<p className="caption">{t("Area = instrument count · Color = mean score · Scores are unitless.")}</p><MeasurementDisclosure title={t("Sector values and keyboard filters")}><TableScroll label={t("Sector summary and accessible filters")}><table><thead><tr><th scope="col">{t("Sector filter")}</th><th scope="col">{t("Instruments")}</th><th scope="col">{t("Mean score")}</th><th scope="col">{t("Overweight stances")}</th><th scope="col">{t("Underweight stances")}</th></tr></thead><tbody>{sectors.map((item) => <tr key={item.sector}><th scope="row"><button className="button" onClick={() => update({ sector: item.sector })}>{sectorName(item.sector, t)}</button></th><td>{number(item.count)}</td><td><Canonical>{formatScore(item.meanScore)}</Canonical></td><td>{number(item.overweight)}</td><td>{number(item.underweight)}</td></tr>)}</tbody></table></TableScroll></MeasurementDisclosure></section>
    <section className="card extremes"><div className="section-heading"><div><p className="eyebrow">{t("Score extremes")}</p><h2>{t("Research shortlist")}</h2></div><span className="muted text-xs">{t("By pool rank")}</span></div><div className="shortlist-grid">{[[t("Top 5"), extremes.slice(0, 5)], [t("Bottom 5"), extremes.slice(-5).reverse()]].map(([label, items]) => <div key={label}><h3>{label}</h3><ol>{items.map((row) => <li key={row.symbol}><Link to={tickerPath(row)} state={{ from }}><span className="symbol">{row.symbol}</span><span className={row.score < 0 ? 'negative' : 'positive'}><Canonical>{formatScore(row.score)}</Canonical> <span aria-hidden="true">↗</span></span></Link></li>)}</ol></div>)}</div></section></div>}
    <section className="card table-card"><div className="section-heading"><div><p className="eyebrow">{t("Instrument universe")}</p><h2>{t("Recommendation leaderboard")}</h2></div><span className="result-count" aria-live="polite"><Message text="{value1} of {value2} instruments" values={{value1: number(filtered.length), value2: number(rows.length)}} /></span></div>
      <div className="filter-bar"><label className="search-field"><Message text="Search instruments{value1}" values={{value1: <input type="search" value={query} onChange={(event) => update({ q: event.target.value })} placeholder={t("Search symbol or name…")} />}} /></label><label><Message text="Sector{value1}" values={{value1: <select aria-label={t("Sector")} value={sector} onChange={(event) => update({ sector: event.target.value })}><option value="">{t("All sectors")}</option>{sectors.map((item) => <option key={item.sector} value={item.sector}>{sectorName(item.sector, t)}</option>)}</select>}} /></label><button className="button clear-button" onClick={() => { setParams({}, { replace: true, flushSync: true }); }}>{t("Clear filters")}</button></div>
      {!isPro && <div className="simple-sort"><label><Message text="Sort candidates{value1}" values={{value1: <select aria-label={t("Sort candidates")} value={`${sortKey}:${sortDir}`} onChange={(event) => { const [sort, dir] = event.target.value.split(':'); update({ sort, dir }); }}>{[['rank', t("Rank")], ['score', t("Score")], ['net_edge_bps', t("Net edge")], ['expected_alpha_bps', t("Expected alpha")], ['coverage', t("Coverage")], ['ret_1d', t("1-day return")]].flatMap(([key, label]) => ['asc', 'desc'].map((dir) => <option key={`${key}:${dir}`} value={`${key}:${dir}`}>{label} · {dir === 'asc' ? t("Ascending") : t("Descending")}</option>))}</select>}} /></label></div>}
      <fieldset className="tier-filters"><legend>{t("Research stance")}</legend>{TIER_ORDER.map((tier) => <label key={tier} className={tiers.includes(tier) ? 'checked' : ''}><input type="checkbox" checked={tiers.includes(tier)} onChange={() => update({ tier: tiers.includes(tier) ? tiers.filter((item) => item !== tier) : [...tiers, tier] })} />{t(tierLabel(tier))}</label>)}</fieldset>
      {filtered.length ? <>{isPro ? <TableScroll label={t("Sortable recommendation leaderboard")}><table className="leaderboard"><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id} scope="col" aria-sort={sortKey === header.id ? sortDir === 'desc' ? 'descending' : 'ascending' : undefined}>{header.column.columnDef.enableSorting ? <button onClick={() => update({ sort: header.id, dir: sortKey === header.id && sortDir === 'asc' ? 'desc' : 'asc' })}>{header.column.columnDef.header}<span aria-hidden="true">{sortKey === header.id ? sortDir === 'asc' ? ' ↑' : ' ↓' : ' ↕'}</span></button> : header.column.columnDef.header}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.original.symbol} tabIndex={0} aria-label={t("Open {value1} research", {value1: row.original.symbol})} onClick={(event) => { if (!event.target.closest('a')) navigate(tickerPath(row.original), { state: { from } }); }} onKeyDown={(event) => { if (event.key === 'Enter' && event.target === event.currentTarget) navigate(tickerPath(row.original), { state: { from } }); }}>{row.getVisibleCells().map((cell) => <td key={cell.id} dir={['rank', 'score', 'net_edge_bps', 'expected_alpha_bps', 'coverage', 'ret_1d'].includes(cell.column.id) ? 'ltr' : undefined} className={['score', 'net_edge_bps', 'expected_alpha_bps'].includes(cell.column.id) ? cell.getValue() < 0 ? 'negative numeric' : 'positive numeric' : ''}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></TableScroll> : <div className="candidate-grid market-candidates">{table.getRowModel().rows.map((row) => <CandidateCard key={row.original.symbol} row={row.original} run={data} from={from} />)}</div>}
      <div className="pagination"><span><Message text="Showing {value1}–{value2} of {value3}" values={{value1: number(pagination.pageIndex * pagination.pageSize + 1), value2: number(Math.min((pagination.pageIndex + 1) * pagination.pageSize, filtered.length)), value3: number(filtered.length)}} /></span><div><button className="button" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()}>{t("← Previous")}</button><span><Message text="Page {value1} of {value2}" values={{value1: number(pagination.pageIndex + 1), value2: number(table.getPageCount())}} /></span><button className="button" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>{t("Next →")}</button></div></div></> : <Empty title={t("No instruments match your filters")} action={<button className="button" onClick={() => setParams({})}>{t("Clear all filters")}</button>}>{t("Try another symbol, sector or research stance.")}</Empty>}
    </section></>;
}
