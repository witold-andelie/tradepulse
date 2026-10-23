import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function RunTracePage({ events }) {
  return (
    <Page title="Run Trace">
      <Card title="Run events">
        <p>Coming soon: execution timeline, event filters, and usage totals.</p>
        <p className="mt-2 text-slate-600">{formatCount(events.length)} trace events available.</p>
      </Card>
    </Page>
  );
}
