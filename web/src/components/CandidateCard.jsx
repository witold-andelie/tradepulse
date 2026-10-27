import { SourceText } from '../i18n/Locale.jsx';
import { poolName, sectorName, factorName } from '../i18n/labels.js';
import { useLocale, Message } from "../i18n/Locale.jsx";
import { Link } from 'react-router-dom';
import { contributionsSorted } from '../lib/data.js';
import { researchRecord } from '../lib/research.js';
import { formatScore } from '../lib/format.js';
import { number, tickerPath, Tier, Badge, Metrics } from './ui.jsx';
export default function CandidateCard({ row, run, from }) {
  const { t, locale } = useLocale();
  const record = researchRecord(run, row.pool, row.symbol);
  const largest = contributionsSorted(row)[0];
  const factor = largest && run.factor_cards.find((card) => card.pool === row.pool && card.factor === largest.factor);
  return <article className="candidate-card" data-instrument={`${row.pool}:${row.symbol}`}>
    <div className="candidate-top"><span><Message text="Pool rank {value1}" values={{value1: number(row.rank)}} /></span><Tier value={row.tier} /></div>
    <h3><Link to={tickerPath(row)} state={{ from }}>{row.symbol}</Link></h3><p className="candidate-name"><SourceText inline>{row.name}</SourceText></p>
    <p className="candidate-sector">{poolName(row.pool, t, record.pool?.label || row.pool)} · {sectorName(row.sector, t)}</p>
    <dl className="candidate-score"><dt>{t("Composite score")}</dt><dd><bdi dir="ltr">{formatScore(row.score)}</bdi></dd></dl>
    {largest ? <p className="candidate-context"><Message text="Largest recorded contribution: {value1} ({value2})." values={{value1: <strong>{factorName(largest.factor, t, factor?.title || largest.factor)}</strong>, value2: formatScore(largest.contribution)}} /></p> : <p className="candidate-context">{t("No factor contributions supplied.")}</p>}
    <div className="candidate-verdict"><Badge tone={record.explanation?.verdict || 'muted'}>{record.explanation?.verdict || t("Explanation unavailable")}</Badge>{record.explanation?.verdict === 'abstained' && <p>{t("The explanation abstained. Inspect the rejected evidence before drawing a conclusion.")}</p>}</div>
    <p className="candidate-provenance"><Message text="{value1}{value2} · As of {value3} · {value4} days" values={{value1: run.data_mode === 'SYNTHETIC' ? t("Fictional instrument · ") : '', value2: run.data_mode, value3: run.as_of, value4: number(row.horizon_days)}} /></p>
    <div className="candidate-actions"><Link className="button primary" to={`${tickerPath(row)}#explanation`} state={{ from }} aria-label={t("Why this stance? {value1}", {value1: row.symbol})}><Message text="Why this stance? {value1}" values={{value1: <span aria-hidden="true">→</span>}} /></Link><Link className="text-link" to={`${tickerPath(row)}#risks`} state={{ from }} aria-label={[t("Risks & limitations"), row.symbol].join(" · ")}>{t("Risks & limitations")}</Link></div>
    <details className="candidate-measurements"><summary>{t("Exact source measurements")}</summary><Metrics items={[["Rank", number(row.rank)], ['Score', formatScore(row.score)]]} /><p><Message text="Source tier: {value1}. Original measurements and evidence are available on the instrument page." values={{value1: row.tier}} /></p></details>
  </article>;
}
