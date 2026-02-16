"use client";

const STAGE_COLORS: Record<string, string> = {
  DISCOVERY: "bg-blue-100 text-blue-700",
  ENGAGING: "bg-purple-100 text-purple-700",
  INTERVIEWING: "bg-indigo-100 text-indigo-700",
  NEGOTIATING: "bg-yellow-100 text-yellow-800",
  OFFER: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  GHOSTED: "bg-orange-100 text-orange-700",
};

interface StageBadgeProps {
  stage: string;
}

export default function StageBadge({ stage }: StageBadgeProps) {
  const colors = STAGE_COLORS[stage] || "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors}`}
    >
      {stage}
    </span>
  );
}
