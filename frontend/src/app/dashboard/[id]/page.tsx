"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/ui/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
  deleteOpportunity,
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
        className="w-4 h-4 rounded-full bg-muted text-muted-foreground text-[10px] font-bold leading-none hover:bg-muted/80 inline-flex items-center justify-center"
        title="Stage descriptions"
      >
        ?
      </button>
      {open && (
        <div className="absolute left-0 top-6 z-20 w-72 rounded-lg border border-border bg-card shadow-xl shadow-primary/5 p-3">
          <p className="text-xs font-medium text-foreground/80 mb-2">Stage meanings:</p>
          <dl className="space-y-1">
            {ALL_STAGES.map((s) => (
              <div key={s} className="flex gap-2">
                <dt className="text-xs font-medium text-muted-foreground min-w-[110px]">
                  {s}
                </dt>
                <dd className="text-xs text-muted-foreground/80">{STAGE_DESCRIPTIONS[s]}</dd>
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
  const [draftLanguage, setDraftLanguage] = useState("auto");
  const [additionalContext, setAdditionalContext] = useState("");
  const [generating, setGenerating] = useState(false);
  const [suggestionModalOpen, setSuggestionModalOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  // Track the suggestion we already showed a modal for, so we don't re-pop on every refresh
  const shownSuggestionRef = useRef<string | null>(null);

  useEffect(() => {
    fetchOpportunityDetail(id)
      .then((data) => {
        setOpp(data);
        // Use pipeline-detected language, fall back to "auto"
        setDraftLanguage(data.detected_language || "auto");
      })
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
      await generateDraft(id, draftType, additionalContext || undefined, draftLanguage === "auto" ? undefined : draftLanguage);
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

  async function handleDeleteOpportunity() {
    try {
      await deleteOpportunity(id);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Delete failed");
      setShowDeleteConfirm(false);
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
      <div className="min-h-screen bg-muted/40">
        <Navbar />
        <div className="flex items-center justify-center py-20">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !opp) {
    return (
      <div className="min-h-screen bg-muted/40">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 py-8">
          <Button variant="ghost" onClick={() => router.back()} className="mb-4">
            &larr; Back
          </Button>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-destructive">{error || "Not found"}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const timeline = buildTimeline();
  const cycleState = deriveCycleState(opp);
  const currentDrafts = getCurrentRoundDrafts(opp);
  const hasFinalDraft = currentDrafts.some((d) => d.is_final);

  return (
    <div className="min-h-screen bg-muted/40">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Back + header */}
        <Button variant="ghost" onClick={() => router.push("/dashboard")} className="-ml-2">
          &larr; Back to Dashboard
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-foreground">
              {opp.company_name || "Unknown Company"}
            </h1>
            <p className="text-muted-foreground">
              {opp.role_title || "Role not extracted"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StageBadge stage={opp.stage} />
            {opp.is_archived && (
              <span className="text-xs text-muted-foreground border border-border rounded px-2 py-0.5">
                Archived
              </span>
            )}
          </div>
        </div>

        {/* Stage Progress Indicator */}
        <StageProgressIndicator currentStage={opp.stage} />

        {/* Stage Suggestion Banner */}
        {opp.suggested_stage && (
          <StageSuggestionBanner
            suggestedStage={opp.suggested_stage}
            reason={opp.suggested_stage_reason}
            onAccept={handleAcceptSuggestion}
            onDismiss={handleDismissSuggestion}
          />
        )}

        {/* Grid: left = details, right = score */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Extracted data */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Extracted Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                {opp.salary_range && (
                  <>
                    <dt className="text-muted-foreground">Salary</dt>
                    <dd className="text-foreground">{opp.salary_range}</dd>
                  </>
                )}
                {opp.work_model && (
                  <>
                    <dt className="text-muted-foreground">Work Model</dt>
                    <dd className="text-foreground">{opp.work_model}</dd>
                  </>
                )}
                {opp.recruiter_name && (
                  <>
                    <dt className="text-muted-foreground">Recruiter</dt>
                    <dd className="text-foreground">
                      {opp.recruiter_name}
                      {opp.recruiter_type && (
                        <span className="text-muted-foreground ml-1">({opp.recruiter_type})</span>
                      )}
                    </dd>
                  </>
                )}
                {opp.recruiter_company && (
                  <>
                    <dt className="text-muted-foreground">Recruiter Co.</dt>
                    <dd className="text-foreground">{opp.recruiter_company}</dd>
                  </>
                )}
                {opp.client_name && (
                  <>
                    <dt className="text-muted-foreground">Client</dt>
                    <dd className="text-foreground">{opp.client_name}</dd>
                  </>
                )}
              </dl>
              {opp.tech_stack.length > 0 && (
                <div>
                  <span className="text-xs text-muted-foreground">Tech Stack</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {opp.tech_stack.map((t) => (
                      <span
                        key={t}
                        className="inline-flex items-center rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {opp.missing_fields.length > 0 && (
                <div className="rounded-lg bg-amber-500/10 border border-amber-500/25 p-2">
                  <span className="text-xs text-amber-400 font-medium">
                    Missing: {opp.missing_fields.join(", ")}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Match score */}
          <div>
            <MatchScoreCard score={opp.match_score} reasoning={opp.match_reasoning} />
          </div>
        </div>

        {/* Stage change + archive */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3 flex-wrap">
              <label className="text-sm text-muted-foreground flex items-center gap-1">
                Change stage: <StageHelpTooltip />
              </label>
              <select
                disabled={stageLoading}
                value={opp.stage}
                onChange={(e) => handleStageChange(e.target.value)}
                className="text-sm border border-input rounded-md px-2 py-1.5 text-foreground bg-background"
              >
                {ALL_STAGES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>

              {confirmUnusual && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-yellow-600 font-medium">Unusual transition detected.</span>
                  <Button
                    variant="link"
                    size="sm"
                    className="text-yellow-700 p-0 h-auto"
                    onClick={() => handleStageChange(confirmUnusual)}
                  >
                    Confirm
                  </Button>
                  <Button
                    variant="link"
                    size="sm"
                    className="text-muted-foreground p-0 h-auto"
                    onClick={() => setConfirmUnusual(null)}
                  >
                    Cancel
                  </Button>
                </div>
              )}

              {!opp.is_archived && TERMINAL_STAGES.has(opp.stage) && (
                <Button variant="outline" size="sm" onClick={handleArchive}>
                  Archive
                </Button>
              )}
              {opp.is_archived && (
                <Button variant="outline" size="sm" onClick={handleUnarchive}>
                  Unarchive
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                className="text-destructive border-destructive/50 hover:bg-destructive/10"
                onClick={() => setShowDeleteConfirm(true)}
              >
                Delete
              </Button>
            </div>

            {showDeleteConfirm && (
              <div className="mt-4 rounded-md bg-destructive/10 border border-destructive/20 p-4">
                <p className="text-sm font-medium text-destructive">
                  Permanently delete this opportunity?
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  This action is irreversible. All related interactions, drafts, and stage history will be deleted.
                </p>
                <div className="flex gap-3 mt-3">
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={handleDeleteOpportunity}
                  >
                    Yes, delete permanently
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowDeleteConfirm(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <Timeline events={timeline} />
          </CardContent>
        </Card>

        {/* Cycle-state-dependent section */}
        {cycleState === "terminal" && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Opportunity Closed</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                This opportunity is in a terminal stage ({opp.stage}).
                {opp.is_archived ? " It has been archived." : " You can archive it from the Actions section above."}
              </p>
              {opp.draft_responses.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-medium text-muted-foreground">Previous Drafts</h3>
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
            </CardContent>
          </Card>
        )}

        {cycleState === "awaiting_followup" && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Awaiting Recruiter Reply</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-4">
                You&apos;ve sent your response. When the recruiter replies, paste their message below
                to trigger a new analysis cycle.
              </p>
              <FollowUpForm
                defaultSource={getDefaultSource(opp)}
                onSubmit={handleSubmitFollowUp}
              />
            </CardContent>
          </Card>
        )}

        {cycleState === "drafting" && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Draft Responses</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <select
                    value={draftType}
                    onChange={(e) => setDraftType(e.target.value)}
                    className="text-sm border border-input rounded-md px-2 py-1.5 text-foreground bg-background"
                  >
                    <option value="EXPRESS_INTEREST">Express Interest</option>
                    <option value="REQUEST_INFO">Request Info</option>
                    <option value="DECLINE">Decline</option>
                  </select>
                  <select
                    value={draftLanguage}
                    onChange={(e) => setDraftLanguage(e.target.value)}
                    className="text-sm border border-input rounded-md px-2 py-1.5 text-foreground bg-background"
                    title="Draft language"
                  >
                    <option value="auto">Auto-detect</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                  </select>
                  <Button
                    onClick={handleGenerateDraft}
                    disabled={generating}
                    size="sm"
                  >
                    {generating ? "Generating..." : "Generate Draft"}
                  </Button>
                </div>
                <textarea
                  value={additionalContext}
                  onChange={(e) => setAdditionalContext(e.target.value)}
                  placeholder="Additional instructions (optional)"
                  rows={2}
                  className="w-full text-sm text-foreground placeholder:text-muted-foreground border border-input rounded-md px-2 py-1.5 focus:ring-2 focus:ring-ring focus:border-ring bg-background"
                />
              </div>

              {currentDrafts.length === 0 ? (
                <p className="text-sm text-muted-foreground">
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
                      hasFinalSibling={hasFinalDraft && !d.is_final}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
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
