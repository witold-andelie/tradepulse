import Trace from './Trace.jsx';

// Keep the agreed page entry point while preserving Huyin's implementation.
export default function RunTracePage({ events }) {
  return <Trace events={events} />;
}
