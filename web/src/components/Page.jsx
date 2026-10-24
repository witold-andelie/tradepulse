import { PageTitle } from './ui.jsx';

// The application shell owns the single main landmark, provenance, run notes and footer.
export default function Page({ title, children }) {
  return <><PageTitle title={title} />{children}</>;
}
