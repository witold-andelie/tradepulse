import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function FactorLabPage({ factorCards }) {
  return (
    <Page title="Factor Lab">
      <Card title="Factor research">
        <p>Coming soon: factor cards, gates, and IC decay charts.</p>
        <p className="mt-2 text-slate-600">{formatCount(factorCards.length)} factor cards across the run.</p>
      </Card>
    </Page>
  );
}
