import { lazy, Suspense } from 'react';
const ChartEngine = lazy(() => import('./ChartEngine.jsx'));
export default function Chart({ label, ...props }) {
  return <figure className="chart-figure"><div role="img" aria-label={label}>
    <Suspense fallback={<div className="skeleton" style={{ height: props.height || 280 }} role="status">Loading visualization…</div>}><ChartEngine {...props} /></Suspense>
  </div><figcaption>{label} Exact values are available in the adjacent table or measurement disclosure.</figcaption></figure>;
}
