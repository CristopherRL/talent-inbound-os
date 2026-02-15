"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DraftResponseCard from "@/components/opportunity/DraftResponseCard";
import MatchScoreCard from "@/components/opportunity/MatchScoreCard";
import StatusBadge from "@/components/opportunity/StatusBadge";
import Timeline, { type TimelineEvent } from "@/components/opportunity/Timeline";
import {
  fetchOpportunityDetail,
  changeStatus,
  archiveOpportunity,
  unarchiveOpportunity,
  generateDraft,
  editDraft,
  deleteDraft,
  type OpportunityDetail,
} from "@/hooks/use-opportunities";

const ALL_STATUSES = [
  "NEW",
  "ANALYZING",
  "ACTION_REQUIRED",
  "REVIEWING",
  "INTERVIEWING",
  "OFFER",
  "REJECTED",
  "GHOSTED",
];

const TERMINAL_STATUSES = new Set(["OFFER", "REJECTED", "GHOSTED"]);

const STATUS_DESCRIPTIONS: Record<string, string> = {
  NEW: "Just received, not yet processed",
  ANALYZING: "Pipeline processing in progress",
  ACTION_REQUIRED: "Needs your attention (data extracted)",
  REVIEWING: "You're reviewing the opportunity details",
  INTERVIEWING: "Interview process started",
  OFFER: "You've received a formal offer",
  REJECTED: "You've decided to pass",
  GHOSTED: "No response from recruiter",
};

function StatusHelpTooltip() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-4 h-4 rounded-full bg-gray-200 text-gray-500 text-[10px] font-bold leading-none hover:bg-gray-300 inline-flex items-center justify-center"
        title="Status descriptions"
      >
        ?
      </button>
      {open && (
        <div className="absolute left-0 top-6 z-20 w-72 rounded-md border border-gray-200 bg-white shadow-lg p-3">
          <p className="text-xs font-medium text-gray-700 mb-2">Status meanings:</p>
          <dl className="space-y-1">
            {ALL_STATUSES.map((s) => (
              <div key={s} className="flex gap-2">
                <dt className="text-xs font-medium text-gray-600 min-w-[110px]">
                  {s.replace("_", " ")}
                </dt>
                <dd className="text-xs text-gray-500">{STATUS_DESCRIPTIONS[s]}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [opp, setOpp] = useState<OpportunityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [confirmUnusual, setConfirmUnusual] = useState<string | null>(null);
  const [draftType, setDraftType] = useState("EXPRESS_INTEREST");
  const [additionalContext, setAdditionalContext] = useState("");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchOpportunityDetail(id)
      .then(setOpp)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleStatusChange(newStatus: string) {
    if (!opp) return;
    setStatusLoading(true);
    try {
      const result = await changeStatus(id, newStatus);
      if (result.is_unusual && !confirmUnusual) {
        setConfirmUnusual(newStatus);
        setStatusLoading(false);
        return;
      }
      // Reload detail
      const updated = await fetchOpportunityDetail(id);
      setOpp(updated);
      setConfirmUnusual(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Status change failed");
    } finally {
      setStatusLoading(false);
    }
  }

  async function handleArchive() {
    try {
      await archiveOpportunity(id);
      const updated = await fetchOpportunityDetail(id);
      setOpp(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Archive failed");
    }
  }

  async function handleUnarchive() {
    try {
      await unarchiveOpportunity(id);
      const updated = await fetchOpportunityDetail(id);
      setOpp(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unarchive failed");
    }
  }

  async function handleGenerateDraft() {
    setGenerating(true);
    try {
      await generateDraft(id, draftType, additionalContext || undefined);
      const updated = await fetchOpportunityDetail(id);
      setOpp(updated);
      setAdditionalContext("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Draft generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function handleSaveDraft(draftId: string, editedContent: string, isFinal: boolean) {
    try {
      await editDraft(id, draftId, editedContent, isFinal);
      const updated = await fetchOpportunityDetail(id);
      setOpp(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Draft save failed");
    }
  }

  async function handleDeleteDraft(draftId: string) {
    try {
      await deleteDraft(id, draftId);
      const updated = await fetchOpportunityDetail(id);
      setOpp(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Draft delete failed");
    }
  }

  function buildTimeline(): TimelineEvent[] {
    if (!opp) return [];
    const events: TimelineEvent[] = [];

    for (const i of opp.interactions) {
      events.push({
        id: i.id,
        type: "interaction",
        timestamp: i.created_at,
        source: i.source,
        interaction_type: i.interaction_type,
        raw_content: i.raw_content,
      });
    }

    for (const t of opp.status_history) {
      events.push({
        id: t.id,
        type: "transition",
        timestamp: t.created_at,
        from_status: t.from_status,
        to_status: t.to_status,
        triggered_by: t.triggered_by,
        is_unusual: t.is_unusual,
        note: t.note ?? undefined,
      });
    }

    events.sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    );
    return events;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (error || !opp) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-3xl mx-auto">
          <button onClick={() => router.back()} className="text-sm text-blue-600 mb-4">
            &larr; Back
          </button>
          <div className="rounded-md bg-red-50 border border-red-200 p-4">
            <p className="text-sm text-red-700">{error || "Not found"}</p>
          </div>
        </div>
      </div>
    );
  }

  const timeline = buildTimeline();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Back + header */}
        <button
          onClick={() => router.push("/dashboard")}
          className="text-sm text-blue-600 hover:text-blue-500 mb-4"
        >
          &larr; Back to Dashboard
        </button>

        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {opp.company_name || "Unknown Company"}
            </h1>
            <p className="text-gray-600">
              {opp.role_title || "Role not extracted"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={opp.status} />
            {opp.is_archived && (
              <span className="text-xs text-gray-400 border border-gray-300 rounded px-2 py-0.5">
                Archived
              </span>
            )}
          </div>
        </div>

        {/* Grid: left = details, right = score */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Extracted data */}
          <div className="lg:col-span-2 bg-white rounded-lg border p-4 space-y-3">
            <h2 className="text-sm font-medium text-gray-900">Extracted Data</h2>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              {opp.salary_range && (
                <>
                  <dt className="text-gray-500">Salary</dt>
                  <dd className="text-gray-900">{opp.salary_range}</dd>
                </>
              )}
              {opp.work_model && (
                <>
                  <dt className="text-gray-500">Work Model</dt>
                  <dd className="text-gray-900">{opp.work_model}</dd>
                </>
              )}
              {opp.recruiter_name && (
                <>
                  <dt className="text-gray-500">Recruiter</dt>
                  <dd className="text-gray-900">
                    {opp.recruiter_name}
                    {opp.recruiter_type && (
                      <span className="text-gray-400 ml-1">({opp.recruiter_type})</span>
                    )}
                  </dd>
                </>
              )}
              {opp.recruiter_company && (
                <>
                  <dt className="text-gray-500">Recruiter Co.</dt>
                  <dd className="text-gray-900">{opp.recruiter_company}</dd>
                </>
              )}
              {opp.client_name && (
                <>
                  <dt className="text-gray-500">Client</dt>
                  <dd className="text-gray-900">{opp.client_name}</dd>
                </>
              )}
            </dl>
            {opp.tech_stack.length > 0 && (
              <div>
                <span className="text-xs text-gray-500">Tech Stack</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {opp.tech_stack.map((t) => (
                    <span
                      key={t}
                      className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {opp.missing_fields.length > 0 && (
              <div className="rounded bg-yellow-50 p-2">
                <span className="text-xs text-yellow-700 font-medium">
                  Missing: {opp.missing_fields.join(", ")}
                </span>
              </div>
            )}
          </div>

          {/* Match score */}
          <div>
            <MatchScoreCard score={opp.match_score} reasoning={opp.match_reasoning} />
          </div>
        </div>

        {/* Status change + archive */}
        <div className="bg-white rounded-lg border p-4 mb-8">
          <h2 className="text-sm font-medium text-gray-900 mb-3">Actions</h2>
          <div className="flex items-center gap-3 flex-wrap">
            <label className="text-sm text-gray-600 flex items-center gap-1">
              Change status: <StatusHelpTooltip />
            </label>
            <select
              disabled={statusLoading}
              value={opp.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-2 py-1.5 text-gray-700 bg-white"
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>

            {/* Unusual transition confirmation */}
            {confirmUnusual && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-yellow-600 font-medium">
                  Unusual transition detected.
                </span>
                <button
                  onClick={() => handleStatusChange(confirmUnusual)}
                  className="text-yellow-700 underline"
                >
                  Confirm
                </button>
                <button
                  onClick={() => setConfirmUnusual(null)}
                  className="text-gray-500"
                >
                  Cancel
                </button>
              </div>
            )}

            {/* Archive/unarchive */}
            {!opp.is_archived && TERMINAL_STATUSES.has(opp.status) && (
              <button
                onClick={handleArchive}
                className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 rounded border border-gray-300"
              >
                Archive
              </button>
            )}
            {opp.is_archived && (
              <button
                onClick={handleUnarchive}
                className="text-sm text-blue-600 hover:text-blue-500 px-3 py-1.5 rounded border border-blue-300"
              >
                Unarchive
              </button>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-lg border p-4 mb-8">
          <h2 className="text-sm font-medium text-gray-900 mb-3">Timeline</h2>
          <Timeline events={timeline} />
        </div>

        {/* Draft responses */}
        <div className="bg-white rounded-lg border p-4">
          <h2 className="text-sm font-medium text-gray-900 mb-3">
            Draft Responses
          </h2>

          {/* Generate new draft */}
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2">
              <select
                value={draftType}
                onChange={(e) => setDraftType(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-2 py-1.5 text-gray-700 bg-white"
              >
                <option value="EXPRESS_INTEREST">Express Interest</option>
                <option value="REQUEST_INFO">Request Info</option>
                <option value="DECLINE">Decline</option>
              </select>
              <button
                onClick={handleGenerateDraft}
                disabled={generating}
                className="text-sm px-4 py-1.5 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {generating ? "Generating..." : "Generate Draft"}
              </button>
            </div>
            <textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Additional instructions (optional) — e.g. 'mencionar que tengo disponibilidad inmediata' or 'ask about equity package'"
              rows={2}
              className="w-full text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md px-2 py-1.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {opp.draft_responses.length === 0 ? (
            <p className="text-sm text-gray-500">
              No drafts yet. Select a response type above and click "Generate Draft".
            </p>
          ) : (
            <div className="space-y-3">
              {opp.draft_responses.map((d) => (
                <DraftResponseCard
                  key={d.id}
                  draft={d}
                  onSave={handleSaveDraft}
                  onDelete={handleDeleteDraft}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
