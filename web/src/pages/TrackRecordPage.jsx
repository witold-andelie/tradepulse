import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function TrackRecordPage({ trackRecord }) {
  const decisions = trackRecord.settled_count + trackRecord.pending_count;
  return (
    <Page title="Track Record">
      <Card title="Research outcomes">
        <p>Coming soon: walk-forward outcomes and score versus outcome charts.</p>
        <p className="mt-2 text-slate-600">{formatCount(decisions)} decisions in the track record.</p>
      </Card>
    </Page>
  );
}
