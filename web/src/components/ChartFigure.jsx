import { useId, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { accessibleChartOption } from '../lib/a11y.js';

/**
 * Every chart in the app goes through this component, so each one has:
 * - a visible title and a one-sentence summary computed from the data (also its accessible name);
 * - ECharts ARIA and decal patterns, and no animation under reduced motion;
 * - a "Show data as table" toggle with the same numbers as an accessible table.
 *
 * Props: title, summary (string computed by the caller from the data), option (ECharts option),
 * columns ([{ key, label }]), rows (array of objects), height (px, default 320), onEvents.
 */
export default function ChartFigure({ title, summary, option, columns, rows, height = 320, onEvents }) {
  const [showTable, setShowTable] = useState(false);
  const tableId = useId();
  return (
    <figure className="rounded-xl border border-slate-200 bg-white p-4">
      <figcaption className="mb-2">
        <span className="block font-semibold text-slate-900">{title}</span>
        <span className="block text-sm text-slate-600">{summary}</span>
      </figcaption>
      <div role="img" aria-label={`${title}. ${summary}`}>
        <ReactECharts option={accessibleChartOption(option)} style={{ height }} onEvents={onEvents}
          notMerge lazyUpdate />
      </div>
      <button type="button" onClick={() => setShowTable((v) => !v)} aria-expanded={showTable}
        aria-controls={tableId}
        className="mt-3 min-h-6 rounded-md px-2 py-1 text-sm font-medium text-blue-800 underline">
        {showTable ? 'Hide data table' : 'Show data as table'}
      </button>
      {showTable && (
        <div id={tableId} className="mt-2 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">{title}: data</caption>
            <thead>
              <tr>{columns.map((c) => <th key={c.key} scope="col" className="border-b px-2 py-1">{c.label}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i}>{columns.map((c) => <td key={c.key} className="border-b px-2 py-1">{row[c.key] ?? '—'}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </figure>
  );
}
