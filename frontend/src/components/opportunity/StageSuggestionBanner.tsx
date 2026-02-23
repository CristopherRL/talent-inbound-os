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
    <div className="rounded-lg bg-primary/10 border border-primary/25 p-3 flex items-center justify-between gap-3">
      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground">
          AI suggests moving to{" "}
          <span className="font-semibold text-primary">{suggestedStage}</span>
          {reason && (
            <span className="text-primary/80">: {reason}</span>
          )}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={handleAccept}
          disabled={loading}
          className="text-sm px-3 py-1 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-50 transition-colors"
        >
          Accept
        </button>
        <button
          onClick={handleDismiss}
          disabled={loading}
          className="text-sm px-3 py-1 rounded-md border border-border text-muted-foreground hover:bg-muted disabled:opacity-50 transition-colors"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
