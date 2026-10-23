import { lazy, Suspense } from 'react';
const ChartEngine = lazy(() => import('./ChartEngine.jsx'));
export default function Chart(props) {
  return <Suspense fallback={<div className="skeleton" style={{ height: props.height || 280 }} role="status">Loading visualization…</div>}><ChartEngine {...props} /></Suspense>;
}
