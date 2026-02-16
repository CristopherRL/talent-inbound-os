"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DraftResponseCard from "@/components/opportunity/DraftResponseCard";
import FollowUpForm from "@/components/opportunity/FollowUpForm";
import MatchScoreCard from "@/components/opportunity/MatchScoreCard";
import StageBadge from "@/components/opportunity/StageBadge";
import StageProgressIndicator from "@/components/opportunity/StageProgressIndicator";
import StageSuggestionBanner from "@/components/opportunity/StageSuggestionBanner";
import StageSuggestionModal from "@/components/opportunity/StageSuggestionModal";
import Timeline, { type TimelineEvent } from "@/components/opportunity/Timeline";
import {
  fetchOpportunityDetail,
  changeStage,
  acceptStageSuggestion,
  dismissStageSuggestion,
  archiveOpportunity,
  unarchiveOpportunity,
  generateDraft,
  editDraft,
  deleteDraft,
  confirmDraftSent,
  submitFollowUp,
  type OpportunityDetail,
} from "@/hooks/use-opportunities";

const ALL_STAGES = [
  "DISCOVERY",
  "ENGAGING",
  "INTERVIEWING",
  "NEGOTIATING",
  "OFFER",
  "REJECTED",
  "GHOSTED",
];

const TERMINAL_STAGES = new Set(["OFFER", "REJECTED", "GHOSTED"]);

const STAGE_DESCRIPTIONS: Record<string, string> = {
  DISCOVERY: "Pipeline analyzed, you're evaluating the opportunity",
  ENGAGING: "Active conversation with the recruiter",
  INTERVIEWING: "Formal interview process started",
  NEGOTIATING: "Discussing terms and compensation",
  OFFER: "You've received a formal offer",
  REJECTED: "You've decided to pass",
  GHOSTED: "No response from recruiter",
};

type CycleState = "processing" | "terminal" | "awaiting_followup" | "drafting";

function deriveCycleState(opp: OpportunityDetail): CycleState {
  if (TERMINAL_STAGES.has(opp.stage) || opp.is_archived) return "terminal";

  // Check if latest interaction is a CANDIDATE_RESPONSE → awaiting follow-up
  const interactions = [...opp.interactions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  if (interactions.length > 0 && interactions[0].interaction_type === "CANDIDATE_RESPONSE") {
    return "awaiting_followup";
  }

  return "drafting";
}

function getCurrentRoundDrafts(opp: OpportunityDetail) {
  // Find the last CANDIDATE_RESPONSE interaction
  const interactions = [...opp.interactions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  const lastSent = interactions.find((i) => i.interaction_type === "CANDIDATE_RESPONSE");

  if (!lastSent) {
    // No sent responses yet — all drafts are current
    return opp.draft_responses;
  }

  // Only show drafts created AFTER the last CANDIDATE_RESPONSE
  const lastSentTime = new Date(lastSent.created_at).getTime();
  return opp.draft_responses.filter(
    (d) => new Date(d.created_at).getTime() > lastSentTime
  );
}

function getDefaultSource(opp: OpportunityDetail): string {
  // Use the source from the original/latest recruiter interaction
  const recruiterInteractions = opp.interactions.filter(
    (i) => i.interaction_type !== "CANDIDATE_RESPONSE"
  );
  if (recruiterInteractions.length > 0) {
    return recruiterInteractions[recruiterInteractions.length - 1].source;
  }
  return "LINKEDIN";
}

function StageHelpTooltip() {
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
        title="Stage descriptions"
      >
        ?
      </button>
      {open && (
        <div className="absolute left-0 top-6 z-20 w-72 rounded-md border border-gray-200 bg-white shadow-lg p-3">
          <p className="text-xs font-medium text-gray-700 mb-2">Stage meanings:</p>
          <dl className="space-y-1">
            {ALL_STAGES.map((s) => (
              <div key={s} className="flex gap-2">
                <dt className="text-xs font-medium text-gray-600 min-w-[110px]">
                  {s}
                </dt>
                <dd className="text-xs text-gray-500">{STAGE_DESCRIPTIONS[s]}</dd>
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
  const [stageLoading, setStageLoading] = useState(false);
  const [confirmUnusual, setConfirmUnusual] = useState<string | null>(null);
  const [draftType, setDraftType] = useState("EXPRESS_INTEREST");
  const [additionalContext, setAdditionalContext] = useState("");
  const [generating, setGenerating] = useState(false);
  const [suggestionModalOpen, setSuggestionModalOpen] = useState(false);
  // Track the suggestion we already showed a modal for, so we don't re-pop on every refresh
  const shownSuggestionRef = useRef<string | null>(null);

  useEffect(() => {
    fetchOpportunityDetail(id)
      .then(setOpp)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  async function refreshDetail() {
    const updated = await fetchOpportunityDetail(id);
    setOpp(updated);
    return updated;
  }

  /**
   * Refresh + show modal if a NEW suggestion appeared (one we haven't shown yet).
   * Called after follow-up submission or any action that may trigger the pipeline.
   */
  async function refreshAndCheckSuggestion() {
    const updated = await fetchOpportunityDetail(id);
    setOpp(updated);
    if (
      updated.suggested_stage &&
      updated.suggested_stage !== shownSuggestionRef.current
    ) {
      shownSuggestionRef.current = updated.suggested_stage;
      setSuggestionModalOpen(true);
    }
    return updated;
  }

  async function handleStageChange(newStage: string) {
    if (!opp) return;
    setStageLoading(true);
    try {
      const result = await changeStage(id, newStage);
      if (result.is_unusual && !confirmUnusual) {
        setConfirmUnusual(newStage);
        setStageLoading(false);
        return;
      }
      await refreshDetail();
      setConfirmUnusual(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Stage change failed");
    } finally {
      setStageLoading(false);
    }
  }

  async function handleAcceptSuggestion() {
    await acceptStageSuggestion(id);
    setSuggestionModalOpen(false);
    await refreshDetail();
  }

  async function handleDismissSuggestion() {
    await dismissStageSuggestion(id);
    setSuggestionModalOpen(false);
    await refreshDetail();
  }

  function handleModalDismiss() {
    // Close modal but keep the inline banner visible (don't call API dismiss)
    setSuggestionModalOpen(false);
  }

  async function handleArchive() {
    try {
      await archiveOpportunity(id);
      await refreshDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Archive failed");
    }
  }

  async function handleUnarchive() {
    try {
      await unarchiveOpportunity(id);
      await refreshDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unarchive failed");
    }
  }

  async function handleGenerateDraft() {
    setGenerating(true);
    try {
      await generateDraft(id, draftType, additionalContext || undefined);
      await refreshDetail();
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
      await refreshDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Draft save failed");
    }
  }

  async function handleDeleteDraft(draftId: string) {
    try {
      await deleteDraft(id, draftId);
      await refreshDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Draft delete failed");
    }
  }

  async function handleConfirmSent(draftId: string) {
    try {
      await confirmDraftSent(id, draftId);
      await refreshDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Confirm sent failed");
    }
  }

  async function handleSubmitFollowUp(rawContent: string, source: string) {
    await submitFollowUp(id, rawContent, source);
    await refreshAndCheckSuggestion();
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

    for (const t of opp.stage_history) {
      events.push({
        id: t.id,
        type: "transition",
        timestamp: t.created_at,
        from_stage: t.from_stage,
        to_stage: t.to_stage,
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
  const cycleState = deriveCycleState(opp);
  const currentDrafts = getCurrentRoundDrafts(opp);

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

        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {opp.company_name || "Unknown Company"}
            </h1>
            <p className="text-gray-600">
              {opp.role_title || "Role not extracted"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StageBadge stage={opp.stage} />
            {opp.is_archived && (
              <span className="text-xs text-gray-400 border border-gray-300 rounded px-2 py-0.5">
                Archived
              </span>
            )}
          </div>
        </div>

        {/* Stage Progress Indicator */}
        <div className="mb-4">
          <StageProgressIndicator currentStage={opp.stage} />
        </div>

        {/* Stage Suggestion Banner */}
        {opp.suggested_stage && (
          <div className="mb-4">
            <StageSuggestionBanner
              suggestedStage={opp.suggested_stage}
              reason={opp.suggested_stage_reason}
              onAccept={handleAcceptSuggestion}
              onDismiss={handleDismissSuggestion}
            />
          </div>
        )}

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

        {/* Stage change + archive */}
        <div className="bg-white rounded-lg border p-4 mb-8">
          <h2 className="text-sm font-medium text-gray-900 mb-3">Actions</h2>
          <div className="flex items-center gap-3 flex-wrap">
            <label className="text-sm text-gray-600 flex items-center gap-1">
              Change stage: <StageHelpTooltip />
            </label>
            <select
              disabled={stageLoading}
              value={opp.stage}
              onChange={(e) => handleStageChange(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-2 py-1.5 text-gray-700 bg-white"
            >
              {ALL_STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
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
                  onClick={() => handleStageChange(confirmUnusual)}
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
            {!opp.is_archived && TERMINAL_STAGES.has(opp.stage) && (
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

        {/* Cycle-state-dependent section */}
        {cycleState === "terminal" && (
          <div className="bg-white rounded-lg border p-4">
            <h2 className="text-sm font-medium text-gray-900 mb-2">Opportunity Closed</h2>
            <p className="text-sm text-gray-500">
              This opportunity is in a terminal stage ({opp.stage}).
              {opp.is_archived ? " It has been archived." : " You can archive it from the Actions section above."}
            </p>
            {/* Still show all drafts (read-only) */}
            {opp.draft_responses.length > 0 && (
              <div className="mt-4 space-y-3">
                <h3 className="text-xs font-medium text-gray-500">Previous Drafts</h3>
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
        )}

        {cycleState === "awaiting_followup" && (
          <div className="bg-white rounded-lg border p-4">
            <h2 className="text-sm font-medium text-gray-900 mb-2">Awaiting Recruiter Reply</h2>
            <p className="text-xs text-gray-500 mb-4">
              You&apos;ve sent your response. When the recruiter replies, paste their message below
              to trigger a new analysis cycle.
            </p>
            <FollowUpForm
              defaultSource={getDefaultSource(opp)}
              onSubmit={handleSubmitFollowUp}
            />
          </div>
        )}

        {cycleState === "drafting" && (
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

            {currentDrafts.length === 0 ? (
              <p className="text-sm text-gray-500">
                No drafts yet. Select a response type above and click &quot;Generate Draft&quot;.
              </p>
            ) : (
              <div className="space-y-3">
                {currentDrafts.map((d) => (
                  <DraftResponseCard
                    key={d.id}
                    draft={d}
                    onSave={handleSaveDraft}
                    onDelete={handleDeleteDraft}
                    onConfirmSent={handleConfirmSent}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stage Suggestion Modal — pops up when a new suggestion arrives */}
      {opp.suggested_stage && (
        <StageSuggestionModal
          open={suggestionModalOpen}
          suggestedStage={opp.suggested_stage}
          reason={opp.suggested_stage_reason}
          onAccept={handleAcceptSuggestion}
          onDismiss={handleModalDismiss}
        />
      )}
    </div>
  );
}
