"use client";

import { useEffect, useRef, useState } from "react";

interface StageSuggestionModalProps {
  open: boolean;
  suggestedStage: string;
  reason: string | null;
  onAccept: () => Promise<void>;
  onDismiss: () => void;
}

export default function StageSuggestionModal({
  open,
  suggestedStage,
  reason,
  onAccept,
  onDismiss,
}: StageSuggestionModalProps) {
  const [loading, setLoading] = useState(false);
  const backdropRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onDismiss();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onDismiss]);

  if (!open) return null;

  async function handleAccept() {
    setLoading(true);
    try {
      await onAccept();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      ref={backdropRef}
      onClick={(e) => {
        if (e.target === backdropRef.current) onDismiss();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <div className="bg-card rounded-xl shadow-2xl shadow-primary/10 max-w-md w-full mx-4 overflow-hidden border border-border">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-5 py-4">
          <h3 className="text-base font-semibold text-white">
            Stage Transition Suggested
          </h3>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          <p className="text-sm text-foreground/80 mb-3">
            The AI pipeline detected signals that this opportunity should advance:
          </p>
          <div className="rounded-lg bg-primary/10 border border-primary/25 px-4 py-3 mb-3">
            <p className="text-sm font-medium text-primary">
              Move to <span className="font-bold">{suggestedStage}</span>
            </p>
            {reason && (
              <p className="text-sm text-primary/80 mt-1">{reason}</p>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            You can also change the stage manually from the Actions section at any time.
          </p>
        </div>

        {/* Footer */}
        <div className="bg-muted/50 px-5 py-3 flex justify-end gap-3 border-t border-border">
          <button
            onClick={onDismiss}
            disabled={loading}
            className="text-sm px-4 py-2 rounded-md border border-border text-foreground hover:bg-muted disabled:opacity-50 transition-colors"
          >
            Decide Later
          </button>
          <button
            onClick={handleAccept}
            disabled={loading}
            className="text-sm px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-50 transition-colors"
          >
            {loading ? "Accepting..." : "Accept"}
          </button>
        </div>
      </div>
    </div>
  );
}
