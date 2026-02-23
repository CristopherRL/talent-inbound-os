"use client";

const STAGE_COLORS: Record<string, string> = {
  DISCOVERY: "bg-blue-500/15 text-blue-400",
  ENGAGING: "bg-indigo-500/15 text-indigo-400",
  INTERVIEWING: "bg-violet-500/15 text-violet-400",
  NEGOTIATING: "bg-amber-500/15 text-amber-400",
  OFFER: "bg-emerald-500/15 text-emerald-400",
  REJECTED: "bg-slate-400/15 text-slate-400",
  DECLINED: "bg-orange-500/15 text-orange-400",
  GHOSTED: "bg-rose-500/15 text-rose-400",
};

interface StageBadgeProps {
  stage: string;
}

export default function StageBadge({ stage }: StageBadgeProps) {
  const colors = STAGE_COLORS[stage] || "bg-muted text-muted-foreground";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors}`}
    >
      {stage}
    </span>
  );
}
