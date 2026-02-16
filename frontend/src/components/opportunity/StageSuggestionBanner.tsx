"use client";

import { useState } from "react";

interface StageSuggestionBannerProps {
  suggestedStage: string;
  reason: string | null;
  onAccept: () => Promise<void>;
  onDismiss: () => Promise<void>;
}

export default function StageSuggestionBanner({
  suggestedStage,
  reason,
  onAccept,
  onDismiss,
}: StageSuggestionBannerProps) {
  const [loading, setLoading] = useState(false);

  async function handleAccept() {
    setLoading(true);
    try {
      await onAccept();
    } finally {
      setLoading(false);
    }
  }

  async function handleDismiss() {
    setLoading(true);
    try {
      await onDismiss();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-md bg-indigo-50 border border-indigo-200 p-3 flex items-center justify-between gap-3">
      <div className="flex-1 min-w-0">
        <p className="text-sm text-indigo-800">
          AI suggests moving to{" "}
          <span className="font-semibold">{suggestedStage}</span>
          {reason && (
            <span className="text-indigo-600">: {reason}</span>
          )}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={handleAccept}
          disabled={loading}
          className="text-sm px-3 py-1 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Accept
        </button>
        <button
          onClick={handleDismiss}
          disabled={loading}
          className="text-sm px-3 py-1 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
