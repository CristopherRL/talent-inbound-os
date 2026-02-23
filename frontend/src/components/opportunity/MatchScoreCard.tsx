"use client";

import { useState } from "react";
import {
  SCORING_THRESHOLD_HIGH,
  SCORING_THRESHOLD_MEDIUM,
} from "@/config/scoring";

interface MatchScoreCardProps {
  score: number | null;
  reasoning: string | null;
}

function scoreColor(score: number): string {
  if (score >= SCORING_THRESHOLD_HIGH)
    return "text-emerald-400 bg-emerald-500/10 border-emerald-500/25";
  if (score >= SCORING_THRESHOLD_MEDIUM)
    return "text-amber-400 bg-amber-500/10 border-amber-500/25";
  return "text-rose-400 bg-rose-500/10 border-rose-500/25";
}

function scoreLabel(score: number): string {
  if (score >= SCORING_THRESHOLD_HIGH) return "Strong Match";
  if (score >= SCORING_THRESHOLD_MEDIUM) return "Moderate Match";
  return "Weak Match";
}

function ringColor(score: number): string {
  if (score >= SCORING_THRESHOLD_HIGH) return "stroke-emerald-500";
  if (score >= SCORING_THRESHOLD_MEDIUM) return "stroke-amber-500";
  return "stroke-rose-500";
}

function ScoreRing({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-20 h-20 flex-shrink-0">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
        <circle
          cx="40"
          cy="40"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          className="text-muted"
        />
        <circle
          cx="40"
          cy="40"
          r={radius}
          fill="none"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={ringColor(score)}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-foreground">{score}</span>
        <span className="text-[10px] text-muted-foreground">/100</span>
      </div>
    </div>
  );
}

export default function MatchScoreCard({
  score,
  reasoning,
}: MatchScoreCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (score === null) {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-medium text-foreground mb-2">Match Score</h3>
        <p className="text-sm text-muted-foreground">
          Score not available. The offer may be missing critical fields or still
          processing.
        </p>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-4 ${scoreColor(score)}`}>
      <h3 className="text-sm font-medium text-foreground mb-3">Match Score</h3>
      <div className="flex items-center gap-3 mb-2">
        <ScoreRing score={score} />
        <span className="text-sm font-semibold">{scoreLabel(score)}</span>
      </div>
      {reasoning && (
        <div className="mt-2 border-t border-current/10 pt-2">
          <p
            className={`text-xs text-foreground/70 leading-relaxed ${
              !expanded ? "line-clamp-3" : ""
            }`}
          >
            {reasoning}
          </p>
          {reasoning.length > 150 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-primary hover:text-primary/80 mt-1 transition-colors"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
