"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/ui/Navbar";
import OpportunityCard, {
  type OpportunityCardData,
} from "@/components/opportunity/OpportunityCard";
import {
  fetchOpportunities,
  fetchStaleOpportunities,
  type OpportunityListItem,
  type StaleItem,
} from "@/hooks/use-opportunities";

type SortField = "date" | "score";

const ALL_STAGES = [
  "DISCOVERY",
  "ENGAGING",
  "INTERVIEWING",
  "NEGOTIATING",
  "OFFER",
  "REJECTED",
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

export default function DashboardPage() {
  const router = useRouter();
  const [opportunities, setOpportunities] = useState<OpportunityListItem[]>([]);
  const [staleIds, setStaleIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortField>("date");
  const [stageFilter, setStageFilter] = useState<string>("");
  const [archivedFilter, setArchivedFilter] = useState<string>("");
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  const sorted = sortOpportunities(opportunities, sortBy);
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const paged = sorted.slice((safePage - 1) * pageSize, safePage * pageSize);

  useEffect(() => {
    async function load() {
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
    return {
      ...opp,
      is_stale: staleIds.has(opp.id),
    };
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action bar */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-medium text-gray-900">Opportunities</h2>
          <div className="flex items-center gap-3">
            {/* Stage filter */}
            <select
              value={stageFilter}
              onChange={(e) => { setStageFilter(e.target.value); setLoading(true); }}
              className="text-sm border border-gray-300 rounded-md px-2 py-1.5 text-gray-700 bg-white"
            >
              <option value="">All Stages</option>
              {ALL_STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            {/* Archived filter */}
            <select
              value={archivedFilter}
              onChange={(e) => { setArchivedFilter(e.target.value); setLoading(true); }}
              className="text-sm border border-gray-300 rounded-md px-2 py-1.5 text-gray-700 bg-white"
            >
              <option value="">Active</option>
              <option value="only">Archived</option>
              <option value="all">All</option>
            </select>

            {/* Sort toggle */}
            {opportunities.length > 1 && (
              <div className="flex items-center rounded-md border border-gray-300 bg-white text-sm">
                <button
                  onClick={() => setSortBy("date")}
                  className={`px-3 py-1.5 rounded-l-md ${sortBy === "date" ? "bg-gray-100 font-medium text-gray-900" : "text-gray-600 hover:text-gray-900"}`}
                >
                  Newest
                </button>
                <button
                  onClick={() => setSortBy("score")}
                  className={`px-3 py-1.5 rounded-r-md border-l border-gray-300 ${sortBy === "score" ? "bg-gray-100 font-medium text-gray-900" : "text-gray-600 hover:text-gray-900"}`}
                >
                  Best Match
                </button>
              </div>
            )}

            <a
              href="/ingest"
              className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              + New Offer
            </a>
          </div>
        </div>

        {/* Stale alerts */}
        {staleIds.size > 0 && (
          <div className="rounded-md bg-orange-50 border border-orange-200 p-3 mb-4">
            <p className="text-sm text-orange-700">
              {staleIds.size} opportunity{staleIds.size > 1 ? "ies" : "y"} may need follow-up (no activity in your configured threshold).
            </p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <p className="text-gray-500">Loading opportunities...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4 mb-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && opportunities.length === 0 && (
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <h3 className="text-base font-medium text-gray-900">
              No opportunities yet
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Start by pasting a recruiter message to create your first
              opportunity.
            </p>
            <a
              href="/ingest"
              className="mt-4 inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
            >
              + New Offer
            </a>
          </div>
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
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>Show</span>
                <select
                  value={pageSize}
                  onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                  className="border border-gray-300 rounded-md px-2 py-1 text-sm text-gray-700 bg-white"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
                <span>per page</span>
                <span className="text-gray-400 ml-2">
                  {sorted.length} total
                </span>
              </div>

              {totalPages > 1 && (
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={safePage <= 1}
                    className="px-3 py-1 text-sm rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Prev
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    {safePage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={safePage >= totalPages}
                    className="px-3 py-1 text-sm rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
