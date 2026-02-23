"use client";

import {
  SCORING_THRESHOLD_HIGH,
  SCORING_THRESHOLD_MEDIUM,
} from "@/config/scoring";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface OpportunityCardData {
  id: string;
  company_name: string | null;
  role_title: string | null;
  stage: string;
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

const STAGE_COLORS: Record<string, string> = {
  DISCOVERY: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  ENGAGING: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
  INTERVIEWING: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  NEGOTIATING: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  OFFER: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  REJECTED: "bg-slate-400/15 text-slate-400 border-slate-400/30",
  DECLINED: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  GHOSTED: "bg-rose-500/15 text-rose-400 border-rose-500/30",
};

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= SCORING_THRESHOLD_HIGH
      ? "bg-emerald-500"
      : score >= SCORING_THRESHOLD_MEDIUM
        ? "bg-amber-500"
        : "bg-rose-500";

  const textColor =
    score >= SCORING_THRESHOLD_HIGH
      ? "text-emerald-400"
      : score >= SCORING_THRESHOLD_MEDIUM
        ? "text-amber-400"
        : "text-rose-400";

  return (
    <div className="flex flex-col items-end gap-1 min-w-[3.5rem]">
      <span className={cn("text-sm font-semibold tabular-nums", textColor)}>
        {score}%
      </span>
      <div className="w-14 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

export default function OpportunityCard({
  opportunity: opp,
  onClick,
}: OpportunityCardProps) {
  const stageClass = STAGE_COLORS[opp.stage] ?? "bg-muted text-muted-foreground border-border";

  return (
    <Card
      onClick={onClick}
      className={cn(
        "cursor-pointer transition-all hover:shadow-lg hover:shadow-primary/5 hover:border-primary/20",
        opp.is_stale && "border-amber-500/25"
      )}
    >
      <CardContent className="p-4 flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-foreground truncate">
              {opp.company_name || "Unknown Company"}
            </h3>
            <span
              className={cn(
                "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
                stageClass
              )}
            >
              {opp.stage}
            </span>
            {opp.is_stale && (
              <Badge
                variant="outline"
                className="border-amber-500/30 text-amber-400 bg-amber-500/10 text-xs"
              >
                Stale
              </Badge>
            )}
            {opp.missing_fields.length > 0 && (
              <Badge
                variant="outline"
                className="border-amber-500/30 text-amber-400 bg-amber-500/10 text-xs"
              >
                {opp.missing_fields.length} missing
              </Badge>
            )}
          </div>

          {/* Role */}
          <p className="text-sm text-muted-foreground truncate">
            {opp.role_title || "Role not extracted yet"}
          </p>

          {/* Tech stack chips */}
          {opp.tech_stack.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {opp.tech_stack.slice(0, 5).map((tech) => (
                <span
                  key={tech}
                  className="inline-flex items-center rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary/80"
                >
                  {tech}
                </span>
              ))}
              {opp.tech_stack.length > 5 && (
                <span className="text-xs text-muted-foreground">
                  +{opp.tech_stack.length - 5} more
                </span>
              )}
            </div>
          )}

          {/* Meta row */}
          <div className="flex items-center gap-3 mt-1.5 flex-wrap">
            {opp.work_model && (
              <span className="text-xs font-medium text-muted-foreground">
                {opp.work_model}
              </span>
            )}
            {opp.recruiter_name && (
              <span className="text-xs text-muted-foreground">
                via {opp.recruiter_name}
              </span>
            )}
            <span className="text-xs text-muted-foreground">
              {new Date(opp.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Right side: score + chevron */}
        <div className="flex items-center gap-3">
          {opp.match_score !== null && <ScoreBar score={opp.match_score} />}
          <svg
            className="w-4 h-4 text-muted-foreground shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}
