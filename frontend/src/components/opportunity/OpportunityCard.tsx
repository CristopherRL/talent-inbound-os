"use client";

import {
  SCORING_THRESHOLD_HIGH,
  SCORING_THRESHOLD_MEDIUM,
} from "@/config/scoring";
import StatusBadge from "./StatusBadge";

export interface OpportunityCardData {
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
  is_stale?: boolean;
}

interface OpportunityCardProps {
  opportunity: OpportunityCardData;
  onClick?: () => void;
}

export default function OpportunityCard({
  opportunity: opp,
  onClick,
}: OpportunityCardProps) {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow p-4 flex items-center justify-between hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="text-sm font-medium text-gray-900 truncate">
            {opp.company_name || "Unknown Company"}
          </h3>
          <StatusBadge status={opp.status} />
          {opp.is_stale && (
            <span className="inline-flex items-center rounded-full bg-orange-50 px-2 py-0.5 text-xs font-medium text-orange-700 border border-orange-200">
              Stale
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 truncate">
          {opp.role_title || "Role not extracted yet"}
        </p>
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
              opp.match_score >= SCORING_THRESHOLD_HIGH
                ? "text-green-600"
                : opp.match_score >= SCORING_THRESHOLD_MEDIUM
                  ? "text-yellow-600"
                  : "text-red-500"
            }`}
          >
            {opp.match_score}%
          </span>
        )}
        <svg
          className="w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </div>
  );
}
