"use client";

const NON_TERMINAL_STAGES = ["DISCOVERY", "ENGAGING", "INTERVIEWING", "NEGOTIATING"];
const TERMINAL_STAGES = new Set(["OFFER", "REJECTED", "GHOSTED"]);

const TERMINAL_COLORS: Record<string, string> = {
  OFFER: "bg-green-100 text-green-700 border-green-200",
  REJECTED: "bg-red-100 text-red-700 border-red-200",
  GHOSTED: "bg-orange-100 text-orange-700 border-orange-200",
};

interface StageProgressIndicatorProps {
  currentStage: string;
}

export default function StageProgressIndicator({ currentStage }: StageProgressIndicatorProps) {
  if (TERMINAL_STAGES.has(currentStage)) {
    const colors = TERMINAL_COLORS[currentStage] || "bg-gray-100 text-gray-700 border-gray-200";
    return (
      <div className={`inline-flex items-center rounded-md border px-3 py-1.5 text-sm font-medium ${colors}`}>
        {currentStage}
      </div>
    );
  }

  const currentIdx = NON_TERMINAL_STAGES.indexOf(currentStage);

  return (
    <div className="flex items-center gap-0">
      {NON_TERMINAL_STAGES.map((stage, idx) => {
        const isCompleted = idx < currentIdx;
        const isCurrent = idx === currentIdx;
        const isFuture = idx > currentIdx;

        return (
          <div key={stage} className="flex items-center">
            {/* Circle */}
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                  isCompleted
                    ? "bg-green-500 text-white"
                    : isCurrent
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-500"
                }`}
              >
                {isCompleted ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={`text-[10px] mt-1 ${
                  isCurrent ? "font-medium text-blue-700" : isFuture ? "text-gray-400" : "text-gray-600"
                }`}
              >
                {stage}
              </span>
            </div>
            {/* Connector line */}
            {idx < NON_TERMINAL_STAGES.length - 1 && (
              <div
                className={`w-12 h-0.5 mx-1 ${
                  idx < currentIdx ? "bg-green-500" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
