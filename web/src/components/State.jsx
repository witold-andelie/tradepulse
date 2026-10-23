export function Loading() {
  return (
    <div role="status" aria-live="polite" className="space-y-3 rounded-xl border border-slate-200 bg-white p-6">
      <p className="text-slate-600">Loading research data…</p>
      <div aria-hidden="true" className="space-y-3 motion-safe:animate-pulse">
        <div className="h-4 w-2/3 rounded bg-slate-200" />
        <div className="h-4 w-full rounded bg-slate-100" />
        <div className="h-4 w-1/2 rounded bg-slate-100" />
      </div>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-900">
      <p>{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-4 rounded-lg bg-red-900 px-4 py-2 font-medium text-white hover:bg-red-800">
          Retry
        </button>
      )}
    </div>
  );
}
