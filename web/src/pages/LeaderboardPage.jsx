import Leaderboard from './Leaderboard.jsx';

// Keep the agreed page entry point while preserving Huyin's implementation.
export default function LeaderboardPage({ run, pool }) {
  return <Leaderboard run={run} pool={pool} />;
}
