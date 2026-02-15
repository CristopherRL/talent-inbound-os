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
    return "text-green-600 bg-green-50 border-green-200";
  if (score >= SCORING_THRESHOLD_MEDIUM)
    return "text-yellow-600 bg-yellow-50 border-yellow-200";
  return "text-red-500 bg-red-50 border-red-200";
}

function scoreLabel(score: number): string {
  if (score >= SCORING_THRESHOLD_HIGH) return "Strong Match";
  if (score >= SCORING_THRESHOLD_MEDIUM) return "Moderate Match";
  return "Weak Match";
}

function ringColor(score: number): string {
  if (score >= SCORING_THRESHOLD_HIGH) return "stroke-green-500";
  if (score >= SCORING_THRESHOLD_MEDIUM) return "stroke-yellow-500";
  return "stroke-red-500";
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
          className="text-gray-200"
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
        <span className="text-lg font-bold text-gray-900">{score}</span>
        <span className="text-[10px] text-gray-500">/100</span>
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
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Match Score</h3>
        <p className="text-sm text-gray-500">
          Score not available. The offer may be missing critical fields or still
          processing.
        </p>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-4 ${scoreColor(score)}`}>
      <h3 className="text-sm font-medium text-gray-900 mb-3">Match Score</h3>
      <div className="flex items-center gap-3 mb-2">
        <ScoreRing score={score} />
        <span className="text-sm font-semibold">{scoreLabel(score)}</span>
      </div>
      {reasoning && (
        <div className="mt-2 border-t border-current/10 pt-2">
          <p
            className={`text-xs text-gray-700 leading-relaxed ${
              !expanded ? "line-clamp-3" : ""
            }`}
          >
            {reasoning}
          </p>
          {reasoning.length > 150 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-blue-600 hover:text-blue-700 mt-1"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
