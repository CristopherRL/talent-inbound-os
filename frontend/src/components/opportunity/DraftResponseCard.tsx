"use client";

import { useState } from "react";

interface DraftResponseData {
  id: string;
  response_type: string;
  generated_content: string;
  edited_content: string | null;
  is_final: boolean;
  is_sent: boolean;
  sent_at: string | null;
  created_at: string;
}

interface DraftResponseCardProps {
  draft: DraftResponseData;
  onSave: (draftId: string, editedContent: string, isFinal: boolean) => Promise<void>;
  onDelete: (draftId: string) => Promise<void>;
  onConfirmSent?: (draftId: string) => Promise<void>;
}

const TYPE_LABELS: Record<string, string> = {
  REQUEST_INFO: "Request Info",
  EXPRESS_INTEREST: "Express Interest",
  DECLINE: "Decline",
};

export default function DraftResponseCard({ draft, onSave, onDelete, onConfirmSent }: DraftResponseCardProps) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(draft.edited_content || draft.generated_content);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const displayText = draft.edited_content || draft.generated_content;

  async function handleSave(markFinal: boolean) {
    setSaving(true);
    try {
      await onSave(draft.id, editText, markFinal);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(displayText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await onDelete(draft.id);
    } finally {
      setDeleting(false);
    }
  }

  async function handleConfirmSent() {
    if (!onConfirmSent) return;
    setConfirming(true);
    try {
      await onConfirmSent(draft.id);
    } finally {
      setConfirming(false);
    }
  }

  // Sent state — read-only display
  if (draft.is_sent) {
    return (
      <div className="border border-green-200 bg-green-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-700">
              {TYPE_LABELS[draft.response_type] || draft.response_type}
            </span>
            <span className="text-xs text-green-700 font-medium bg-green-100 px-1.5 py-0.5 rounded">
              Sent
            </span>
          </div>
          <span className="text-xs text-gray-400">
            Sent {draft.sent_at ? new Date(draft.sent_at).toLocaleString() : ""}
          </span>
        </div>
        <p className="text-sm text-gray-600 whitespace-pre-wrap">{displayText}</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-700">
            {TYPE_LABELS[draft.response_type] || draft.response_type}
          </span>
          {draft.is_final && (
            <span className="text-xs text-green-600 font-medium bg-green-50 px-1.5 py-0.5 rounded">
              Final
            </span>
          )}
          {draft.edited_content && !draft.is_final && (
            <span className="text-xs text-blue-500">Edited</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {new Date(draft.created_at).toLocaleString()}
          </span>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="text-gray-300 hover:text-red-500 disabled:opacity-50"
            title="Delete draft"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {editing ? (
        <div className="space-y-2">
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            rows={8}
            className="w-full text-sm text-gray-900 border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleSave(false)}
              disabled={saving}
              className="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Draft"}
            </button>
            <button
              onClick={() => handleSave(true)}
              disabled={saving}
              className="text-xs px-3 py-1.5 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Mark as Final"}
            </button>
            <button
              onClick={() => { setEditing(false); setEditText(displayText); }}
              className="text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-600 whitespace-pre-wrap mb-3">
            {displayText}
          </p>
          <div className="flex items-center gap-2">
            {!draft.is_final && (
              <button
                onClick={() => setEditing(true)}
                className="text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
              >
                Edit
              </button>
            )}
            <button
              onClick={handleCopy}
              className="text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
            {draft.is_final && !draft.is_sent && onConfirmSent && (
              <button
                onClick={handleConfirmSent}
                disabled={confirming}
                className="text-xs px-3 py-1.5 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {confirming ? "Confirming..." : "I've Sent This"}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export type { DraftResponseData };
