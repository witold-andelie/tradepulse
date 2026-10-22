// Tier vocabulary (task B1). Tiers are research stances, never orders.

export const TIER_ORDER = ['STRONG_OVERWEIGHT', 'OVERWEIGHT', 'NEUTRAL', 'UNDERWEIGHT', 'AVOID', 'NO_CALL'];

/**
 * Human label: STRONG_OVERWEIGHT -> "Strong overweight", OVERWEIGHT -> "Overweight",
 * NEUTRAL -> "Neutral", UNDERWEIGHT -> "Underweight", AVOID -> "Avoid", NO_CALL -> "No call".
 * An unknown value throws an Error (a contract violation must be visible, not hidden).
 */
export function tierLabel(tier) {
  throw new Error('B1: implement tierLabel');
}

/**
 * Visual tone used for colour AND an icon/text cue (never colour alone):
 * STRONG_OVERWEIGHT -> "strong-positive", OVERWEIGHT -> "positive", NEUTRAL -> "neutral",
 * UNDERWEIGHT -> "negative", AVOID -> "strong-negative", NO_CALL -> "muted". Unknown throws.
 */
export function tierTone(tier) {
  throw new Error('B1: implement tierTone');
}
