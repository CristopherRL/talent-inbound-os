"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiPost, DuplicateError } from "@/lib/api";
import Navbar from "@/components/ui/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useProfileGate } from "@/hooks/use-profile-gate";

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
  const { profileComplete, loading: profileLoading, missingFields } = useProfileGate();
  const [rawContent, setRawContent] = useState("");
  const [source, setSource] = useState("LINKEDIN");
  const [error, setError] = useState<string | null>(null);
  const [duplicateOpportunityId, setDuplicateOpportunityId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const charCount = rawContent.length;
  const isEmpty = rawContent.trim().length === 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setDuplicateOpportunityId(null);

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
      if (err instanceof DuplicateError) {
        setDuplicateOpportunityId(err.existingOpportunityId);
      } else {
        const message =
          err instanceof Error ? err.message : "Failed to submit message.";
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-muted/40">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!profileLoading && !profileComplete && (
          <Card className="mb-6 border-amber-500/25 bg-amber-500/10">
            <CardContent className="p-6 text-center">
              <h3 className="text-base font-semibold text-amber-300">Profile incomplete</h3>
              <p className="mt-1 text-sm text-amber-400">
                Complete your profile before submitting offers so we can score them.
              </p>
              {missingFields.length > 0 && (
                <p className="mt-1 text-xs text-amber-400/80">
                  Missing: {missingFields.join(", ")}
                </p>
              )}
              <Button asChild className="mt-3 bg-amber-600 hover:bg-amber-500">
                <a href="/profile">Go to Profile</a>
              </Button>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Paste Recruiter Message</CardTitle>
            <p className="text-sm text-muted-foreground">
              Copy-paste the recruiter&apos;s message below and select where it came from.
              The AI pipeline will classify, extract data, and score the opportunity.
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Source
                </label>
                <Select value={source} onValueChange={setSource}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SOURCES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label
                  htmlFor="raw_content"
                  className="block text-sm font-medium text-foreground mb-1.5"
                >
                  Message
                </label>
                <Textarea
                  id="raw_content"
                  rows={12}
                  value={rawContent}
                  onChange={(e) => setRawContent(e.target.value)}
                  maxLength={MAX_LENGTH}
                  placeholder="Paste the recruiter's message here..."
                  className="resize-y"
                />
                <div className="mt-1 text-right">
                  <span
                    className={`text-xs ${
                      charCount > MAX_LENGTH * 0.9 ? "text-destructive" : "text-muted-foreground"
                    }`}
                  >
                    {charCount.toLocaleString()} / {MAX_LENGTH.toLocaleString()} characters
                  </span>
                </div>
              </div>

              {duplicateOpportunityId && (
                <div className="rounded-md bg-amber-500/10 border border-amber-500/25 p-3">
                  <p className="text-sm text-amber-300">
                    A similar offer from the same company and role is already tracked.{" "}
                    <Link
                      href={`/dashboard/${duplicateOpportunityId}`}
                      className="font-semibold underline hover:text-amber-200 transition-colors"
                    >
                      View existing opportunity →
                    </Link>
                  </p>
                </div>
              )}

              {error && (
                <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3">
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                disabled={loading || isEmpty || !profileComplete}
                className="w-full"
              >
                {loading ? "Submitting..." : "Submit for Analysis"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
