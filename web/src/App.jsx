import { LocaleProvider, LanguageSelector, SourceText } from './i18n/Locale.jsx';
import { poolName } from './i18n/labels.js';
import { useLocale, Message } from "./i18n/Locale.jsx";
import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { createBrowserRouter, Link, NavLink, Navigate, Outlet, RouterProvider, useLocation } from 'react-router-dom';
import { RunProvider, useRunOutput } from './hooks/useRunOutput.jsx';
import { dataModeBanner } from './lib/data.js';
import { apiBase } from './api/client.js';
import { Badge, ErrorState, Loading, NotFound, number } from './components/ui.jsx';
import { PresentationProvider, usePresentation } from './hooks/usePresentation.jsx';
import { ViewSwitch, ResearchGuide } from './components/ResearchGuide.jsx';
import Leaderboard from './pages/LeaderboardPage.jsx';
const Discover = lazy(() => import('./pages/Discover.jsx'));
const Detail = lazy(() => import('./pages/TickerPage.jsx'));
const Factors = lazy(() => import('./pages/FactorLabPage.jsx'));
const Regime = lazy(() => import('./pages/RegimePage.jsx'));
const TrackRecord = lazy(() => import('./pages/TrackRecordPage.jsx'));
const Trace = lazy(() => import('./pages/RunTracePage.jsx'));
const links = [['/factors', 'Factor Lab', '◫'], ['/regime', 'Market Regime', '◎'], ['/track-record', 'Track Record', '↗'], ['/trace', 'Run Trace', '≋']];
function Layout() {
  const { t, locale } = useLocale();
  const { data, loading, error, retry } = useRunOutput();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const { marketPath, rememberMarket } = usePresentation();
  const location = useLocation();
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [location.pathname]);
  useEffect(() => { if (data?.pools.some((pool) => location.pathname === `/pool/${pool.pool}`)) rememberMarket(location.pathname + location.search); }, [data, location.pathname, location.search, rememberMarket]);
  useEffect(() => {
    const title = location.pathname.startsWith('/pool/') ? t("Leaderboard") : location.pathname.startsWith('/ticker/') ? t("Instrument Research") : location.pathname === '/discover' ? t("Discover") : links.find(([path]) => path === location.pathname)?.[1] || t("Not Found");
    document.title = t("{value1} · TradePulse", {value1: t(title)});
  }, [location.pathname, loading, t]);
  const banner = data ? dataModeBanner(data.data_mode) : null;
  const researchTools = data && (<div className="workspace-tools">{data.warnings.length > 0 && <details className="run-warnings"><summary><Message text="Run limitations · {value1} notice(s)" values={{value1: number(data.warnings.length)}} /></summary><ul>{data.warnings.map((warning, i) => <li key={i}><SourceText>{warning}</SourceText></li>)}</ul></details>}<ResearchGuide /></div>);
  return <div className="app"><a className="skip-link" href="#main-content">{t("Skip to main content")}</a>
    <aside className="sidebar" onKeyDown={(event) => { if (open && event.key === 'Escape') { setOpen(false); menuRef.current?.focus(); } }}><Link className="brand" to="/discover" aria-label={t("TradePulse Discover")}><span className="brand-mark" aria-hidden="true">⌁</span><span>TradePulse<small>{t("AGENT RESEARCH")}</small></span></Link>
      <button ref={menuRef} className="menu-toggle button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="workspace-nav">{open ? t("Close menu") : t("Menu")}</button>
      <nav id="workspace-nav" className={open ? 'navigation open' : 'navigation'} aria-label={t("Main navigation")}><p className="nav-label">{t("WORKSPACE")}</p><NavLink to="/discover" className={({ isActive }) => `nav-link ${isActive ? 'selected' : ''}`}><Message text="{value1}Discover" values={{value1: <span aria-hidden="true">✧</span>}} /></NavLink><NavLink to={marketPath} aria-current={location.pathname.startsWith('/pool/') || location.pathname.startsWith('/ticker/') ? 'page' : undefined} className={`nav-link ${location.pathname.startsWith('/pool/') || location.pathname.startsWith('/ticker/') ? 'selected' : ''}`}><Message text="{value1}Explore Markets" values={{value1: <span aria-hidden="true">▤</span>}} /></NavLink>{links.map(([path, label, icon]) => <NavLink key={path} to={path} className={({ isActive }) => `nav-link ${isActive ? 'selected' : ''}`}><span aria-hidden="true">{icon}</span>{t(label)}</NavLink>)}</nav>
      <div className="sidebar-note"><span className="status-dot" />{t("ONE EVIDENCE BASE")}<p><Message text="Financial intelligence{value1}everyone can understand." values={{value1: <br />}} /></p><small><Message text="Research and education only.{value1}No trade execution." values={{value1: <br />}} /></small></div></aside>
    <div className="workspace"><header className="topbar"><div className="workspace-label"><span className="agent-indicator" aria-hidden="true">✧</span><span><Message text="Research workspace {value1}" values={{value1: <span className="muted">/ {apiBase ? t("API connection") : t("Fixture demo")}</span>}} /></span></div><div className="topbar-controls"><LanguageSelector /><ViewSwitch /></div></header>
      {banner?.show && <div className={`mode-banner ${banner.tone}`} role="note"><span aria-hidden="true">⚑</span><strong>{t(banner.text)}</strong></div>}
      {!data && <div className="mode-banner info">{apiBase ? t("API configured · awaiting validated run data.") : t("Fixture demo · loading synthetic research data.")}</div>}
      {data && <><div className="run-info"><span><Message text="AS OF {value1}" values={{value1: <strong><bdi dir="ltr">{data.as_of}</bdi></strong>}} /></span><span><Message text="HORIZON {value1}" values={{value1: <strong><Message text="{value1} days" values={{value1: number(data.horizon_days)}} /></strong>}} /></span><span><Message text="MODE {value1}" values={{value1: <strong>{data.data_mode}</strong>}} /></span><span className="run-id"><Message text="RUN {value1}" values={{value1: <strong>{data.run_id}</strong>}} /></span></div>{location.pathname !== '/discover' && <nav className="pool-tabs" aria-label={t("Asset pools")}>{data.pools.map((pool) => <NavLink key={pool.pool} to={`/pool/${pool.pool}`} className={({ isActive }) => isActive ? 'active' : ''}>{poolName(pool.pool, t, pool.label)}<span>{number(data.recommendations.filter((row) => row.pool === pool.pool).length)}</span></NavLink>)}</nav>}</>}
      <main id="main-content" tabIndex={-1} className="main-content">{loading ? <Loading /> : error ? <ErrorState error={error} retry={retry} /> : <>{location.pathname !== '/discover' && researchTools}<Suspense fallback={<Loading />}><Outlet /></Suspense>{location.pathname === '/discover' && researchTools}</>}</main>
      <footer><strong>TradePulse</strong>{data && locale !== 'en' && <p>{t('Research and education only. Tiers are research stances, not orders. No investment advice or trade execution.')}</p>}<p>{data?.disclaimer ? <SourceText>{data.disclaimer}</SourceText> : t("Research and education only. Tiers are research stances, not orders. No investment advice or trade execution.")}</p><span>{t("Evidence before conviction.")}</span></footer></div></div>;
}
function RouteFailure() {
  const { t } = useLocale();
  useEffect(() => { document.title = `${t('This page could not be displayed')} · TradePulse`; }, [t]);
  return <><header className="topbar"><span>{t('Research workspace')}</span><div className="topbar-controls"><LanguageSelector /><ViewSwitch /></div></header><main id="main-content" className="main-content"><NotFound title={t('This page could not be displayed')} /></main></>;
}
const router = createBrowserRouter([{ element: <Layout />, errorElement: <RouteFailure />, children: [
  { index: true, element: <Navigate to="/pool/us_equity" replace /> },
  { path: '/discover', element: <Discover /> },
  { path: '/pool/:pool', element: <Leaderboard /> }, { path: '/ticker/:pool/:symbol', element: <Detail /> },
  { path: '/factors', element: <Factors /> }, { path: '/regime', element: <Regime /> },
  { path: '/track-record', element: <TrackRecord /> }, { path: '/trace', element: <Trace /> },
  { path: '*', element: <NotFound /> },
] }], { future: { v7_relativeSplatPath: true, v7_fetcherPersist: true, v7_normalizeFormMethod: true, v7_partialHydration: true, v7_skipActionErrorRevalidation: true } });
export default function App() { return <LocaleProvider><PresentationProvider><RunProvider><RouterProvider router={router} future={{ v7_startTransition: true }} /></RunProvider></PresentationProvider></LocaleProvider>; }
