import Detail from './Detail.jsx';

// Keep the agreed page entry point while preserving Huyin's implementation.
export default function TickerPage({ run, pool, symbol }) {
  return <Detail run={run} pool={pool} symbol={symbol} />;
}
