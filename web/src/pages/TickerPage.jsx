import { Link } from 'react-router-dom';
import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function TickerPage({ run, pool, symbol }) {
  const recommendation = run.recommendations.find((row) => row.pool === pool && row.symbol === symbol);
  return (
    <Page title={recommendation ? `${recommendation.symbol} · ${recommendation.name}` : 'Ticker not found'}>
      <Card title="Ticker detail">
        {recommendation ? (
          <>
            <p>Coming soon: contribution charts and evidence-backed explanations.</p>
            <p className="mt-2 text-slate-600">{formatCount(recommendation.contributions.length)} factor contributions available.</p>
          </>
        ) : (
          <>
            <p>No recommendation matches this pool and symbol in the current run.</p>
            <Link className="mt-3 inline-block text-blue-800 underline" to="/">Return home</Link>
          </>
        )}
      </Card>
    </Page>
  );
}
