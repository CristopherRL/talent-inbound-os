"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Navbar from "@/components/ui/Navbar";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import OpportunityCard, {
  type OpportunityCardData,
} from "@/components/opportunity/OpportunityCard";
import {
  fetchOpportunities,
  fetchStaleOpportunities,
  type OpportunityListItem,
  type StaleItem,
} from "@/hooks/use-opportunities";
import { useProfileGate } from "@/hooks/use-profile-gate";

type SortField = "date" | "score";

const ALL_STAGES = [
  "DISCOVERY",
  "ENGAGING",
  "INTERVIEWING",
  "NEGOTIATING",
  "OFFER",
  "REJECTED",
  "DECLINED",
  "GHOSTED",
];

function sortOpportunities(
  items: OpportunityListItem[],
  field: SortField,
): OpportunityListItem[] {
  return [...items].sort((a, b) => {
    if (field === "score") {
      const sa = a.match_score ?? -1;
      const sb = b.match_score ?? -1;
      return sb - sa;
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [opportunities, setOpportunities] = useState<OpportunityListItem[]>([]);
  const [staleIds, setStaleIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortField>("date");
  const [stageFilter, setStageFilter] = useState<string>(
    searchParams.get("stage") ?? ""
  );
  const [archivedFilter, setArchivedFilter] = useState<string>("");
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const { profileComplete, tooltipMessage } = useProfileGate();

  const sorted = sortOpportunities(opportunities, sortBy);
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const paged = sorted.slice((safePage - 1) * pageSize, safePage * pageSize);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const params: { stage?: string; archived?: string } = {};
        if (stageFilter) params.stage = stageFilter;
        if (archivedFilter) params.archived = archivedFilter;

        const [opps, stale] = await Promise.all([
          fetchOpportunities(params),
          fetchStaleOpportunities().catch(() => [] as StaleItem[]),
        ]);
        setOpportunities(opps);
        setStaleIds(new Set(stale.map((s) => s.id)));
        setCurrentPage(1);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to load opportunities.";
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [stageFilter, archivedFilter]);

  function toCardData(opp: OpportunityListItem): OpportunityCardData {
    return { ...opp, is_stale: staleIds.has(opp.id) };
  }

  return (
    <div className="min-h-screen bg-muted/40">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action bar */}
        <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
          <h2 className="text-xl font-semibold text-foreground">Opportunities</h2>
          <div className="flex flex-wrap items-center gap-3">
            {/* Stage filter */}
            <select
              value={stageFilter}
              onChange={(e) => { setStageFilter(e.target.value); }}
              className="text-sm border border-input rounded-md px-2 py-1.5 text-foreground bg-background"
            >
              <option value="">All Stages</option>
              {ALL_STAGES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            {/* Archived filter */}
            <select
              value={archivedFilter}
              onChange={(e) => { setArchivedFilter(e.target.value); }}
              className="text-sm border border-input rounded-md px-2 py-1.5 text-foreground bg-background"
            >
              <option value="">Active</option>
              <option value="only">Archived</option>
              <option value="all">All</option>
            </select>

            {/* Sort toggle */}
            {opportunities.length > 1 && (
              <div className="flex items-center rounded-md border border-input bg-background text-sm overflow-hidden">
                <button
                  onClick={() => setSortBy("date")}
                  className={`px-3 py-1.5 ${sortBy === "date" ? "bg-muted font-medium" : "text-muted-foreground hover:text-foreground"}`}
                >
                  Newest
                </button>
                <button
                  onClick={() => setSortBy("score")}
                  className={`px-3 py-1.5 border-l border-input ${sortBy === "score" ? "bg-muted font-medium" : "text-muted-foreground hover:text-foreground"}`}
                >
                  Best Match
                </button>
              </div>
            )}

            {profileComplete ? (
              <Button asChild>
                <Link href="/ingest">+ New Offer</Link>
              </Button>
            ) : (
              <Button disabled title={tooltipMessage}>
                + New Offer
              </Button>
            )}
          </div>
        </div>

        {/* Stale alert */}
        {staleIds.size > 0 && (
          <div className="rounded-lg bg-amber-500/10 border border-amber-500/25 p-3 mb-4">
            <p className="text-sm text-amber-400">
              {staleIds.size} opportunit{staleIds.size > 1 ? "ies" : "y"} may need follow-up.
            </p>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Empty state */}
        {!loading && !error && opportunities.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center">
              <h3 className="text-base font-semibold text-foreground mb-2">
                No opportunities yet
              </h3>
              {profileComplete ? (
                <>
                  <p className="text-sm text-muted-foreground mb-4">
                    Start by pasting a recruiter message to create your first opportunity.
                  </p>
                  <Button asChild>
                    <Link href="/ingest">+ New Offer</Link>
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground mb-4">
                    Before adding offers, complete your profile so we can score opportunities against your preferences.
                  </p>
                  <Button asChild>
                    <Link href="/profile">Complete Profile</Link>
                  </Button>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Required: Name, Professional Title, 3+ Skills, Minimum Salary, Work Model
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Opportunity list */}
        {!loading && opportunities.length > 0 && (
          <>
            <div className="space-y-3">
              {paged.map((opp) => (
                <OpportunityCard
                  key={opp.id}
                  opportunity={toCardData(opp)}
                  onClick={() => router.push(`/dashboard/${opp.id}`)}
                />
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-6">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>Show</span>
                <select
                  value={pageSize}
                  onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                  className="border border-input rounded-md px-2 py-1 text-sm bg-background"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
                <span>per page · {sorted.length} total</span>
              </div>

              {totalPages > 1 && (
                <div className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={safePage <= 1}
                  >
                    Prev
                  </Button>
                  <span className="px-3 text-sm text-muted-foreground">
                    {safePage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={safePage >= totalPages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-muted/40" />}>
      <DashboardContent />
    </Suspense>
  );
}
