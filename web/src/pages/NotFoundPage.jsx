import { Link } from 'react-router-dom';
import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function NotFoundPage({ run }) {
  return (
    <Page title="Page not found">
      <Card title="This address is unavailable">
        <p>Return home to browse the current run. More research views are coming soon.</p>
        <p className="mt-2 text-slate-600">{formatCount(run.pools.length)} pools available.</p>
        <Link className="mt-3 inline-block text-blue-800 underline" to="/">Return home</Link>
      </Card>
    </Page>
  );
}
