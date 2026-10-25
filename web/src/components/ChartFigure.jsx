import { useLocale, Message, Canonical } from "../i18n/Locale.jsx";
import { lazy, Suspense, useId, useState } from 'react';

const ChartEngine = lazy(() => import('./ChartEngine.jsx'));

/** Shared figure for both page generations; the renderer keeps Huyin's modular imports. */
export default function ChartFigure({ title, summary, label, columns, rows, height = 280, ...props }) {
  const { t, locale } = useLocale();
  const [showTable, setShowTable] = useState(false);
  const tableId = useId();
  const description = summary || label;
  const tableProvided = Array.isArray(columns) && Array.isArray(rows);
  return <figure className="chart-figure">
    {title && <h3>{t(title)}</h3>}
    <div role="img" aria-label={[t(title || ''), description].filter(Boolean).join('. ')}>
      <Suspense fallback={<div className="skeleton" style={{ height }} role="status">{t("Loading visualization…")}</div>}>
        <ChartEngine {...props} height={height} />
      </Suspense>
    </div>
    <figcaption>{description}{!tableProvided && t(" Exact values are available in the adjacent table or measurement disclosure.")}</figcaption>
    {tableProvided && <>
      <button className="button" type="button" aria-expanded={showTable} aria-controls={tableId}
        onClick={() => setShowTable((value) => !value)}>{showTable ? t("Hide data table") : t("Show data as table")}</button>
      {showTable && <div id={tableId} className="table-scroll" role="region" aria-label={title || description} tabIndex={0}>
        <table><caption>{title || description}{t(": data")}</caption>
          <thead><tr>{columns.map((column) => <th key={column.key} scope="col">{t(column.label)}</th>)}</tr></thead>
          <tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column.key}><Canonical>{row[column.key] ?? '—'}</Canonical></td>)}</tr>)}</tbody>
        </table>
      </div>}
    </>}
  </figure>;
}
