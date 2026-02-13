"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";

interface OpportunityItem {
  id: string;
  company_name: string | null;
  role_title: string | null;
  status: string;
  match_score: number | null;
  missing_fields: string[];
  tech_stack: string[];
  work_model: string | null;
  recruiter_name: string | null;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  NEW: "bg-gray-100 text-gray-700",
  ANALYZING: "bg-blue-100 text-blue-700",
  ACTION_REQUIRED: "bg-yellow-100 text-yellow-800",
  REVIEWING: "bg-purple-100 text-purple-700",
  INTERVIEWING: "bg-indigo-100 text-indigo-700",
  OFFER: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  GHOSTED: "bg-orange-100 text-orange-700",
};

export default function DashboardPage() {
  const router = useRouter();
  const [opportunities, setOpportunities] = useState<OpportunityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOpportunities() {
      try {
        const data = await apiGet<OpportunityItem[]>("/opportunities");
        setOpportunities(data);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to load opportunities.";
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    fetchOpportunities();
  }, []);

  async function handleLogout() {
    try {
      await apiPost("/auth/logout");
    } catch {
      // Even if the API call fails, redirect
    }
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">
            Talent Inbound OS
          </h1>
          <div className="flex items-center gap-4">
            <a
              href="/profile"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Profile
            </a>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded border border-gray-300 hover:border-gray-400"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action bar */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-medium text-gray-900">Opportunities</h2>
          <a
            href="/ingest"
            className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            + New Offer
          </a>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <p className="text-gray-500">Loading opportunities...</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4 mb-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Empty state */}
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
          <div className="space-y-3">
            {opportunities.map((opp) => (
              <div
                key={opp.id}
                className="bg-white rounded-lg shadow p-4 flex items-center justify-between hover:shadow-md transition-shadow"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {opp.company_name || "Unknown Company"}
                    </h3>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[opp.status] || "bg-gray-100 text-gray-700"}`}
                    >
                      {opp.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 truncate">
                    {opp.role_title || "Role not extracted yet"}
                  </p>
                  {/* Tech stack chips */}
                  {opp.tech_stack.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {opp.tech_stack.slice(0, 5).map((tech) => (
                        <span
                          key={tech}
                          className="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                        >
                          {tech}
                        </span>
                      ))}
                      {opp.tech_stack.length > 5 && (
                        <span className="text-xs text-gray-400">
                          +{opp.tech_stack.length - 5} more
                        </span>
                      )}
                    </div>
                  )}
                  <div className="flex items-center gap-4 mt-1">
                    {opp.work_model && (
                      <span className="text-xs text-gray-500 font-medium">
                        {opp.work_model}
                      </span>
                    )}
                    {opp.recruiter_name && (
                      <span className="text-xs text-gray-400">
                        via {opp.recruiter_name}
                      </span>
                    )}
                    <span className="text-xs text-gray-400">
                      {new Date(opp.created_at).toLocaleDateString()}
                    </span>
                    {opp.missing_fields.length > 0 && (
                      <span className="text-xs text-yellow-600">
                        {opp.missing_fields.length} missing field
                        {opp.missing_fields.length > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  {opp.match_score !== null && (
                    <span
                      className={`text-sm font-semibold ${
                        opp.match_score >= 70
                          ? "text-green-600"
                          : opp.match_score >= 40
                            ? "text-yellow-600"
                            : "text-red-500"
                      }`}
                    >
                      {opp.match_score}%
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
