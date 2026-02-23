"use client";

import { useState } from "react";

interface FollowUpFormProps {
  defaultSource: string;
  onSubmit: (rawContent: string, source: string) => Promise<void>;
}

const SOURCES = [
  { value: "LINKEDIN", label: "LinkedIn" },
  { value: "EMAIL", label: "Email" },
  { value: "FREELANCE_PLATFORM", label: "Freelance Platform" },
  { value: "OTHER", label: "Other" },
];

export default function FollowUpForm({ defaultSource, onSubmit }: FollowUpFormProps) {
  const [content, setContent] = useState("");
  const [source, setSource] = useState(defaultSource || "LINKEDIN");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) {
      setError("Please paste the recruiter's follow-up message");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(content.trim(), source);
      setContent("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit follow-up");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-foreground/80 mb-1">
          Recruiter&apos;s follow-up message
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste the recruiter's reply here..."
          rows={5}
          className="w-full text-sm text-foreground bg-muted/50 placeholder:text-muted-foreground border border-border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
        />
      </div>
      <div className="flex items-center gap-3">
        <div>
          <label className="block text-xs text-muted-foreground mb-1">Source</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="text-sm border border-border rounded-md px-2 py-1.5 text-foreground bg-card"
          >
            {SOURCES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            disabled={submitting || !content.trim()}
            className="text-sm px-4 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-50 mt-4 transition-colors"
          >
            {submitting ? "Submitting..." : "Submit Follow-Up"}
          </button>
        </div>
      </div>
      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}
    </form>
  );
}
