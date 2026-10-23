import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function RegimePage({ regimes }) {
  return (
    <Page title="Regime">
      <Card title="Market fragility">
        <p>Coming soon: regime indicators, history, and lift evidence.</p>
        <p className="mt-2 text-slate-600">{formatCount(regimes.length)} pool regimes available.</p>
      </Card>
    </Page>
  );
}
