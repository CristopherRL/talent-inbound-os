/**
 * Scoring thresholds — loaded from environment variables.
 *
 * Change these values in .env (or .env.local) to adjust what
 * constitutes a Strong / Moderate / Weak match without touching code.
 *
 *   NEXT_PUBLIC_SCORING_THRESHOLD_HIGH=70
 *   NEXT_PUBLIC_SCORING_THRESHOLD_MEDIUM=40
 */

export const SCORING_THRESHOLD_HIGH = Number(
  process.env.NEXT_PUBLIC_SCORING_THRESHOLD_HIGH ?? 70,
);

export const SCORING_THRESHOLD_MEDIUM = Number(
  process.env.NEXT_PUBLIC_SCORING_THRESHOLD_MEDIUM ?? 40,
);
