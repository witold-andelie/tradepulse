import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { filterRecommendations } from '../lib/data.js';
import { formatCount } from '../lib/format.js';

export default function LeaderboardPage({ run, pool }) {
  const summary = run.pools.find((entry) => entry.pool === pool);
  const rows = filterRecommendations(run.recommendations, { pool });
  return (
    <Page title={summary.label}>
      <Card title="Leaderboard">
        <p>Coming soon: rankings, filters, and sector views.</p>
        <p className="mt-2 text-slate-600">{formatCount(rows.length)} recommendations in this pool.</p>
      </Card>
    </Page>
  );
}
