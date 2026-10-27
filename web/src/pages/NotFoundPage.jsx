import { useLocale, Message } from "../i18n/Locale.jsx";
import { Link } from 'react-router-dom';
import Card from '../components/Card.jsx';
import Page from '../components/Page.jsx';
import { formatCount } from '../lib/format.js';

export default function NotFoundPage({ run }) {
  const { t, locale } = useLocale();
  return (
    <Page title={t("Page not found")}>
      <Card title={t("This address is unavailable")}>
        <p>{t("Return home to browse the current run. More research views are coming soon.")}</p>
        <p className="mt-2 text-slate-600"><Message text="{value1} pools available." values={{value1: formatCount(run.pools.length)}} /></p>
        <Link className="mt-3 inline-block text-blue-800 underline" to="/">{t("Return home")}</Link>
      </Card>
    </Page>
  );
}
