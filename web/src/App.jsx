import {
  createBrowserRouter, Link, Navigate, NavLink, Outlet, RouterProvider, useParams,
} from 'react-router-dom';
import { RunOutputProvider, useRunOutput } from './api/useRunOutput.js';
import { useTrace } from './api/useTrace.js';
import Badge from './components/Badge.jsx';
import Page from './components/Page.jsx';
import { ErrorState, Loading } from './components/State.jsx';
import { formatCount } from './lib/format.js';
import LeaderboardPage from './pages/LeaderboardPage.jsx';
import TickerPage from './pages/TickerPage.jsx';
import FactorLabPage from './pages/FactorLabPage.jsx';
import RegimePage from './pages/RegimePage.jsx';
import TrackRecordPage from './pages/TrackRecordPage.jsx';
import RunTracePage from './pages/RunTracePage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';

const navigation = [
  ['/pool/us_equity', 'US equities'],
  ['/pool/eu_equity', 'European equities'],
  ['/pool/crypto', 'Crypto'],
  ['/factors', 'Factor Lab'],
  ['/regime', 'Regime'],
  ['/track-record', 'Track Record'],
  ['/trace', 'Run Trace'],
];

function Layout() {
  const { data: run } = useRunOutput();
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:block focus:p-3">Skip to main content</a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
          <Link to="/" className="text-xl font-bold tracking-tight text-slate-950">TradePulse</Link>
          <nav aria-label="Main navigation" className="mt-4 flex flex-wrap gap-2">
            {navigation.map(([to, label]) => (
              <NavLink key={to} to={to} className={({ isActive }) => `rounded-lg px-3 py-2 text-sm font-medium ${isActive
                ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'}`}>
                {label}
              </NavLink>
            ))}
          </nav>
          {run && (
            <dl aria-label="Run information" className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
              <div><dt className="inline text-slate-500">As of: </dt><dd className="inline"><time dateTime={run.as_of}>{run.as_of}</time></dd></div>
              <div className="min-w-0 break-all"><dt className="inline text-slate-500">Run: </dt><dd className="inline font-mono">{run.run_id}</dd></div>
              <div><dt className="inline text-slate-500">Horizon: </dt><dd className="inline">{formatCount(run.horizon_days)} days</dd></div>
              <div><dt className="sr-only">Data mode</dt><dd><Badge tone={run.data_mode === 'SYNTHETIC' ? 'warning' : 'info'} label={run.data_mode} /></dd></div>
            </dl>
          )}
        </div>
      </header>
      <Outlet />
    </div>
  );
}

function RunRoute({ children }) {
  const { data, error, loading, reload } = useRunOutput();
  if (loading) return <Page title="Loading run"><Loading /></Page>;
  if (error) return <Page title="Run unavailable"><ErrorState message={error} onRetry={reload} /></Page>;
  return children(data);
}

function PoolRoute({ ticker = false }) {
  const { pool, symbol } = useParams();
  return (
    <RunRoute>
      {(run) => {
        if (!run.pools.some((entry) => entry.pool === pool)) return <NotFoundPage run={run} />;
        return ticker ? <TickerPage run={run} pool={pool} symbol={symbol} /> : <LeaderboardPage run={run} pool={pool} />;
      }}
    </RunRoute>
  );
}

function TraceRoute({ run }) {
  const { events, error, loading } = useTrace(run.run_id);
  const { reload } = useRunOutput();
  if (loading) return <Page title="Run Trace"><Loading /></Page>;
  if (error) return <Page title="Run Trace"><ErrorState message={error} onRetry={reload} /></Page>;
  return <RunTracePage events={events} />;
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/pool/us_equity" replace /> },
      { path: '/pool/:pool', element: <PoolRoute /> },
      { path: '/ticker/:pool/:symbol', element: <PoolRoute ticker /> },
      { path: '/factors', element: <RunRoute>{(run) => <FactorLabPage factorCards={run.factor_cards} />}</RunRoute> },
      { path: '/regime', element: <RunRoute>{(run) => <RegimePage regimes={run.regimes} />}</RunRoute> },
      { path: '/track-record', element: <RunRoute>{(run) => <TrackRecordPage trackRecord={run.track_record} />}</RunRoute> },
      { path: '/trace', element: <RunRoute>{(run) => <TraceRoute run={run} />}</RunRoute> },
      { path: '*', element: <RunRoute>{(run) => <NotFoundPage run={run} />}</RunRoute> },
    ],
  },
], { future: { v7_relativeSplatPath: true } });

export default function App() {
  return (
    <RunOutputProvider>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </RunOutputProvider>
  );
}
