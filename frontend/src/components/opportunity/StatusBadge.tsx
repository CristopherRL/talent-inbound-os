"use client";

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

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status] || "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors}`}
    >
      {status.replace("_", " ")}
    </span>
  );
}
