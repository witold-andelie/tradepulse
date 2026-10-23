import { Link } from 'react-router-dom';
import { contributionsSorted } from '../lib/data.js';
import { researchRecord } from '../lib/research.js';
import { formatScore } from '../lib/format.js';
import { number, tickerPath, Tier, Badge, Metrics } from './ui.jsx';
export default function CandidateCard({ row, run, from }) {
  const record = researchRecord(run, row.pool, row.symbol);
  const largest = contributionsSorted(row)[0];
  const factor = largest && run.factor_cards.find((card) => card.pool === row.pool && card.factor === largest.factor);
  return <article className="candidate-card" data-instrument={`${row.pool}:${row.symbol}`}>
    <div className="candidate-top"><span>Pool rank {number(row.rank)}</span><Tier value={row.tier} /></div>
    <h3><Link to={tickerPath(row)} state={{ from }}>{row.symbol}</Link></h3><p className="candidate-name">{row.name}</p>
    <p className="candidate-sector">{record.pool?.label || row.pool} · {row.sector}</p>
    <dl className="candidate-score"><dt>Composite score</dt><dd>{formatScore(row.score)}</dd></dl>
    {largest ? <p className="candidate-context">Largest recorded contribution: <strong>{factor?.title || largest.factor}</strong> ({formatScore(largest.contribution)}).</p> : <p className="candidate-context">No factor contributions supplied.</p>}
    <div className="candidate-verdict"><Badge tone={record.explanation?.verdict || 'muted'}>{record.explanation?.verdict || 'Explanation unavailable'}</Badge>{record.explanation?.verdict === 'abstained' && <p>The explanation abstained. Inspect the rejected evidence before drawing a conclusion.</p>}</div>
    <p className="candidate-provenance">{run.data_mode === 'SYNTHETIC' ? 'Fictional instrument · ' : ''}{run.data_mode} · As of {run.as_of} · {number(row.horizon_days)} days</p>
    <div className="candidate-actions"><Link className="button primary" to={`${tickerPath(row)}#explanation`} state={{ from }} aria-label={`Why this stance? ${row.symbol}`}>Why this stance? <span aria-hidden="true">→</span></Link><Link className="text-link" to={`${tickerPath(row)}#risks`} state={{ from }} aria-label={`Risks and limitations for ${row.symbol}`}>Risks & limitations</Link></div>
    <details className="candidate-measurements"><summary>Exact source measurements</summary><Metrics items={[["Rank", number(row.rank)], ['Score', formatScore(row.score)]]} /><p>Source tier: {row.tier}. Original measurements and evidence are available on the instrument page.</p></details>
  </article>;
}
