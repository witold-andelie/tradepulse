// Tier vocabulary (task B1). Tiers are research stances, never orders.

export const TIER_ORDER = ['STRONG_OVERWEIGHT', 'OVERWEIGHT', 'NEUTRAL', 'UNDERWEIGHT', 'AVOID', 'NO_CALL'];

/**
 * Human label: STRONG_OVERWEIGHT -> "Strong overweight", OVERWEIGHT -> "Overweight",
 * NEUTRAL -> "Neutral", UNDERWEIGHT -> "Underweight", AVOID -> "Avoid", NO_CALL -> "No call".
 * An unknown value throws an Error (a contract violation must be visible, not hidden).
 */
export function tierLabel(tier) {
  switch (tier) {
    case 'STRONG_OVERWEIGHT': return 'Strong overweight';
    case 'OVERWEIGHT': return 'Overweight';
    case 'NEUTRAL': return 'Neutral';
    case 'UNDERWEIGHT': return 'Underweight';
    case 'AVOID': return 'Avoid';
    case 'NO_CALL': return 'No call';
    default: throw new Error(`Unknown tier: ${tier}`);
  }
}

/**
 * Visual tone used for colour AND an icon/text cue (never colour alone):
 * STRONG_OVERWEIGHT -> "strong-positive", OVERWEIGHT -> "positive", NEUTRAL -> "neutral",
 * UNDERWEIGHT -> "negative", AVOID -> "strong-negative", NO_CALL -> "muted". Unknown throws.
 */
export function tierTone(tier) {
  switch (tier) {
    case 'STRONG_OVERWEIGHT': return 'strong-positive';
    case 'OVERWEIGHT': return 'positive';
    case 'NEUTRAL': return 'neutral';
    case 'UNDERWEIGHT': return 'negative';
    case 'AVOID': return 'strong-negative';
    case 'NO_CALL': return 'muted';
    default: throw new Error(`Unknown tier: ${tier}`);
  }
}
