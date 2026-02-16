"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import Navbar from "@/components/ui/Navbar";

const SOURCES = [
  { value: "LINKEDIN", label: "LinkedIn" },
  { value: "EMAIL", label: "Email" },
  { value: "FREELANCE_PLATFORM", label: "Freelance Platform" },
  { value: "OTHER", label: "Other" },
];

const MAX_LENGTH = 50000;

interface SubmitResponse {
  interaction_id: string;
  opportunity_id: string;
  stage: string;
  message: string;
}

export default function IngestPage() {
  const router = useRouter();
  const [rawContent, setRawContent] = useState("");
  const [source, setSource] = useState("LINKEDIN");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const charCount = rawContent.length;
  const isEmpty = rawContent.trim().length === 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (isEmpty) {
      setError("Please paste a recruiter message before submitting.");
      return;
    }

    setLoading(true);
    try {
      await apiPost<SubmitResponse>("/ingestion/messages", {
        raw_content: rawContent,
        source,
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to submit message.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-1">
            Paste Recruiter Message
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            Copy-paste the recruiter&apos;s message below and select where it
            came from. The AI pipeline will classify, extract data, and score
            the opportunity.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Source selector */}
            <div>
              <label
                htmlFor="source"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Source
              </label>
              <select
                id="source"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                {SOURCES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Message textarea */}
            <div>
              <label
                htmlFor="raw_content"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Message
              </label>
              <textarea
                id="raw_content"
                rows={12}
                value={rawContent}
                onChange={(e) => setRawContent(e.target.value)}
                maxLength={MAX_LENGTH}
                placeholder="Paste the recruiter's message here..."
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-y"
              />
              <div className="flex justify-between mt-1">
                <span
                  className={`text-xs ${
                    charCount > MAX_LENGTH * 0.9
                      ? "text-red-500"
                      : "text-gray-400"
                  }`}
                >
                  {charCount.toLocaleString()} / {MAX_LENGTH.toLocaleString()}{" "}
                  characters
                </span>
              </div>
            </div>

            {/* Error display */}
            {error && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || isEmpty}
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Submitting..." : "Submit for Analysis"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
