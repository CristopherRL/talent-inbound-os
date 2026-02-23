"use client";

import { AgentStep } from "@/hooks/use-pipeline-progress";

const AGENT_LABELS: Record<string, string> = {
  guardrail: "PII Sanitization",
  gatekeeper: "Classification",
  extractor: "Data Extraction",
};

interface PipelineProgressProps {
  steps: AgentStep[];
  isComplete: boolean;
}

export function PipelineProgress({ steps, isComplete }: PipelineProgressProps) {
  return (
    <div className="space-y-2">
      {steps.map((step) => (
        <div key={step.agent} className="flex items-center gap-3">
          {/* Status icon */}
          <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
            {step.status === "completed" ? (
              <span className="text-emerald-500 text-sm font-bold">&#10003;</span>
            ) : step.status === "started" ? (
              <span className="animate-spin text-primary text-sm">&#9696;</span>
            ) : (
              <span className="text-muted-foreground/40 text-sm">&#9679;</span>
            )}
          </div>

          {/* Step label + summary */}
          <div className="flex-1 min-w-0">
            <p
              className={`text-sm font-medium ${
                step.status === "completed"
                  ? "text-emerald-400"
                  : step.status === "started"
                    ? "text-primary"
                    : "text-muted-foreground/60"
              }`}
            >
              {AGENT_LABELS[step.agent] || step.agent}
            </p>
            {step.resultSummary && (
              <p className="text-xs text-muted-foreground truncate">
                {step.resultSummary}
              </p>
            )}
          </div>
        </div>
      ))}

      {isComplete && (
        <p className="text-xs text-emerald-400 font-medium mt-2">
          Pipeline complete
        </p>
      )}
    </div>
  );
}
