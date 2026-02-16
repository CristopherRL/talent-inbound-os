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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-indigo-600 px-5 py-4">
          <h3 className="text-base font-semibold text-white">
            Stage Transition Suggested
          </h3>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          <p className="text-sm text-gray-700 mb-3">
            The AI pipeline detected signals that this opportunity should advance:
          </p>
          <div className="rounded-md bg-indigo-50 border border-indigo-200 px-4 py-3 mb-3">
            <p className="text-sm font-medium text-indigo-900">
              Move to <span className="font-bold">{suggestedStage}</span>
            </p>
            {reason && (
              <p className="text-sm text-indigo-700 mt-1">{reason}</p>
            )}
          </div>
          <p className="text-xs text-gray-500">
            You can also change the stage manually from the Actions section at any time.
          </p>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-5 py-3 flex justify-end gap-3">
          <button
            onClick={onDismiss}
            disabled={loading}
            className="text-sm px-4 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Decide Later
          </button>
          <button
            onClick={handleAccept}
            disabled={loading}
            className="text-sm px-4 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Accepting..." : "Accept"}
          </button>
        </div>
      </div>
    </div>
  );
}
