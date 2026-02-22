"use client";

const NON_TERMINAL_STAGES = ["DISCOVERY", "ENGAGING", "INTERVIEWING", "NEGOTIATING"];
const TERMINAL_STAGES = new Set(["OFFER", "REJECTED", "GHOSTED"]);

const TERMINAL_COLORS: Record<string, string> = {
  OFFER: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  REJECTED: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  GHOSTED: "bg-amber-500/15 text-amber-400 border-amber-500/30",
};

interface StageProgressIndicatorProps {
  currentStage: string;
}

export default function StageProgressIndicator({ currentStage }: StageProgressIndicatorProps) {
  if (TERMINAL_STAGES.has(currentStage)) {
    const colors = TERMINAL_COLORS[currentStage] || "bg-muted text-muted-foreground border-border";
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
                    ? "bg-emerald-500 text-white"
                    : isCurrent
                      ? "bg-primary text-white shadow-md shadow-primary/30"
                      : "bg-muted text-muted-foreground"
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
                  isCurrent ? "font-medium text-primary" : isFuture ? "text-muted-foreground/60" : "text-muted-foreground"
                }`}
              >
                {stage}
              </span>
            </div>
            {/* Connector line */}
            {idx < NON_TERMINAL_STAGES.length - 1 && (
              <div
                className={`w-12 h-0.5 mx-1 ${
                  idx < currentIdx ? "bg-emerald-500" : "bg-border"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
