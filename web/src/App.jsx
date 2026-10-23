import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { createBrowserRouter, Link, NavLink, Navigate, Outlet, RouterProvider, useLocation } from 'react-router-dom';
import { RunProvider, useRunOutput } from './hooks/useRunOutput.jsx';
import { dataModeBanner } from './lib/data.js';
import { apiBase } from './api/client.js';
import { Badge, ErrorState, Loading, NotFound, number } from './components/ui.jsx';
import { PresentationProvider, usePresentation } from './hooks/usePresentation.jsx';
import { ViewSwitch, ResearchGuide } from './components/ResearchGuide.jsx';
import Leaderboard from './pages/Leaderboard.jsx';
const Discover = lazy(() => import('./pages/Discover.jsx'));
const Detail = lazy(() => import('./pages/Detail.jsx'));
const Factors = lazy(() => import('./pages/Factors.jsx'));
const Regime = lazy(() => import('./pages/Regime.jsx'));
const TrackRecord = lazy(() => import('./pages/TrackRecord.jsx'));
const Trace = lazy(() => import('./pages/Trace.jsx'));
const links = [['/factors', 'Factor Lab', '◫'], ['/regime', 'Market Regime', '◎'], ['/track-record', 'Track Record', '↗'], ['/trace', 'Run Trace', '≋']];
function Layout() {
  const { data, loading, error, retry } = useRunOutput();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const { marketPath, rememberMarket } = usePresentation();
  const location = useLocation();
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [location.pathname]);
  useEffect(() => { if (data?.pools.some((pool) => location.pathname === `/pool/${pool.pool}`)) rememberMarket(location.pathname + location.search); }, [data, location.pathname, location.search, rememberMarket]);
  useEffect(() => {
    const title = location.pathname.startsWith('/pool/') ? 'Leaderboard' : location.pathname.startsWith('/ticker/') ? 'Instrument Research' : location.pathname === '/discover' ? 'Discover' : links.find(([path]) => path === location.pathname)?.[1] || 'Not Found';
    document.title = `${title} · TradePulse`;
  }, [location.pathname, loading]);
  const banner = data ? dataModeBanner(data.data_mode) : null;
  const researchTools = data && (<div className="workspace-tools">{data.warnings.length > 0 && <details className="run-warnings"><summary>Run limitations · {number(data.warnings.length)} notice(s)</summary><ul>{data.warnings.map((warning, i) => <li key={i}>{warning}</li>)}</ul></details>}<ResearchGuide /></div>);
  return <div className="app"><a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className="sidebar" onKeyDown={(event) => { if (open && event.key === 'Escape') { setOpen(false); menuRef.current?.focus(); } }}><Link className="brand" to="/discover" aria-label="TradePulse Discover"><span className="brand-mark" aria-hidden="true">⌁</span><span>TradePulse<small>AGENT RESEARCH</small></span></Link>
      <button ref={menuRef} className="menu-toggle button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="workspace-nav">{open ? 'Close menu' : 'Menu'}</button>
      <nav id="workspace-nav" className={open ? 'navigation open' : 'navigation'} aria-label="Main navigation"><p className="nav-label">WORKSPACE</p><NavLink to="/discover" className={({ isActive }) => `nav-link ${isActive ? 'selected' : ''}`}><span aria-hidden="true">✧</span>Discover</NavLink><NavLink to={marketPath} aria-current={location.pathname.startsWith('/pool/') || location.pathname.startsWith('/ticker/') ? 'page' : undefined} className={`nav-link ${location.pathname.startsWith('/pool/') || location.pathname.startsWith('/ticker/') ? 'selected' : ''}`}><span aria-hidden="true">▤</span>Explore Markets</NavLink>{links.map(([path, label, icon]) => <NavLink key={path} to={path} className={({ isActive }) => `nav-link ${isActive ? 'selected' : ''}`}><span aria-hidden="true">{icon}</span>{label}</NavLink>)}</nav>
      <div className="sidebar-note"><span className="status-dot" /> ONE EVIDENCE BASE<p>Financial intelligence<br />everyone can understand.</p><small>Research and education only.<br />No trade execution.</small></div></aside>
    <div className="workspace"><header className="topbar"><div className="workspace-label"><span className="agent-indicator" aria-hidden="true">✧</span><span>Research workspace <span className="muted">/ {apiBase ? 'API connection' : 'Fixture demo'}</span></span></div><ViewSwitch /></header>
      {banner?.show && <div className={`mode-banner ${banner.tone}`} role="note"><span aria-hidden="true">⚑</span><strong>{banner.text}</strong></div>}
      {!data && <div className="mode-banner info">{apiBase ? 'API configured · awaiting validated run data.' : 'Fixture demo · loading synthetic research data.'}</div>}
      {data && <><div className="run-info"><span>AS OF <strong>{data.as_of}</strong></span><span>HORIZON <strong>{number(data.horizon_days)} days</strong></span><span>MODE <strong>{data.data_mode}</strong></span><span className="run-id">RUN <strong>{data.run_id}</strong></span></div>{location.pathname !== '/discover' && <nav className="pool-tabs" aria-label="Asset pools">{data.pools.map((pool) => <NavLink key={pool.pool} to={`/pool/${pool.pool}`} className={({ isActive }) => isActive ? 'active' : ''}>{pool.label}<span>{number(data.recommendations.filter((row) => row.pool === pool.pool).length)}</span></NavLink>)}</nav>}</>}
      <main id="main-content" tabIndex={-1} className="main-content">{loading ? <Loading /> : error ? <ErrorState error={error} retry={retry} /> : <>{location.pathname !== '/discover' && researchTools}<Suspense fallback={<Loading />}><Outlet /></Suspense>{location.pathname === '/discover' && researchTools}</>}</main>
      <footer><strong>TradePulse</strong><p>{data?.disclaimer || 'Research and education only. Tiers are research stances, not orders. No investment advice or trade execution.'}</p><span>Evidence before conviction.</span></footer></div></div>;
}
const router = createBrowserRouter([{ element: <Layout />, errorElement: <NotFound title="This page could not be displayed" />, children: [
  { index: true, element: <Navigate to="/pool/us_equity" replace /> },
  { path: '/discover', element: <Discover /> },
  { path: '/pool/:pool', element: <Leaderboard /> }, { path: '/ticker/:pool/:symbol', element: <Detail /> },
  { path: '/factors', element: <Factors /> }, { path: '/regime', element: <Regime /> },
  { path: '/track-record', element: <TrackRecord /> }, { path: '/trace', element: <Trace /> },
  { path: '*', element: <NotFound /> },
] }], { future: { v7_relativeSplatPath: true, v7_fetcherPersist: true, v7_normalizeFormMethod: true, v7_partialHydration: true, v7_skipActionErrorRevalidation: true } });
export default function App() { return <PresentationProvider><RunProvider><RouterProvider router={router} future={{ v7_startTransition: true }} /></RunProvider></PresentationProvider>; }
