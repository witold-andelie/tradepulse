import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useRunOutput } from '../api/useRunOutput.js';
import { documentTitle } from '../lib/a11y.js';
import { dataModeBanner } from '../lib/data.js';
import { formatCount } from '../lib/format.js';

export default function Page({ title, children }) {
  const { data: run } = useRunOutput();
  const banner = run ? dataModeBanner(run.data_mode) : null;
  const heading = useRef(null);
  const { pathname } = useLocation();

  // On every route change: name the browser tab and move focus to the new page's heading, so
  // keyboard and screen-reader users land at the start of the new content.
  useEffect(() => {
    document.title = documentTitle(title);
    heading.current?.focus();
  }, [title, pathname]);

  return (
    <>
      <main id="main-content" tabIndex={-1} className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6 sm:px-6">
        {banner?.show && (
          <div role="note" aria-label="Data mode" className={`rounded-lg border px-4 py-3 font-medium ${banner.tone === 'warning'
            ? 'border-yellow-400 bg-yellow-100 text-yellow-950'
            : 'border-blue-300 bg-blue-50 text-blue-950'}`}>
            {banner.text}
          </div>
        )}
        <h1 ref={heading} tabIndex={-1} className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h1>
        {children}
        {run && (
          <details className="rounded-lg border border-slate-200 bg-white p-4">
            <summary className="cursor-pointer font-medium text-slate-800">Run notes ({formatCount(run.warnings.length)})</summary>
            {run.warnings.length > 0 ? (
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
                {run.warnings.map((warning, index) => <li key={index}>{warning}</li>)}
              </ul>
            ) : <p className="mt-3 text-sm text-slate-700">No run warnings reported.</p>}
          </details>
        )}
      </main>
      {run && (
        <footer className="mx-auto w-full max-w-7xl border-t border-slate-200 px-4 py-4 text-sm text-slate-700 sm:px-6">
          {run.disclaimer}
        </footer>
      )}
    </>
  );
}
