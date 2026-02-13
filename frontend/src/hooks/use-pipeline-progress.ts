"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { connectSSE, SSEEvent } from "@/lib/sse";

export interface AgentStep {
  agent: string;
  status: "pending" | "started" | "completed";
  resultSummary: string;
  timestamp: string | null;
}

interface PipelineProgress {
  steps: AgentStep[];
  isComplete: boolean;
  finalStatus: string | null;
  opportunityId: string | null;
}

const INITIAL_STEPS: AgentStep[] = [
  { agent: "guardrail", status: "pending", resultSummary: "", timestamp: null },
  { agent: "gatekeeper", status: "pending", resultSummary: "", timestamp: null },
  { agent: "extractor", status: "pending", resultSummary: "", timestamp: null },
];

export function usePipelineProgress(interactionId: string | null): PipelineProgress {
  const [steps, setSteps] = useState<AgentStep[]>(INITIAL_STEPS);
  const [isComplete, setIsComplete] = useState(false);
  const [finalStatus, setFinalStatus] = useState<string | null>(null);
  const [opportunityId, setOpportunityId] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  const handleEvent = useCallback((event: SSEEvent) => {
    if (event.event === "agent_progress") {
      const { agent, status, result_summary } = event.data as {
        agent: string;
        status: string;
        result_summary: string;
        timestamp: string;
      };
      setSteps((prev) =>
        prev.map((step) =>
          step.agent === agent
            ? {
                ...step,
                status: status as AgentStep["status"],
                resultSummary: result_summary || "",
                timestamp: new Date().toISOString(),
              }
            : step,
        ),
      );
    }

    if (event.event === "pipeline_complete") {
      const { opportunity_id, final_status } = event.data as {
        opportunity_id: string;
        final_status: string;
      };
      setIsComplete(true);
      setFinalStatus(final_status);
      setOpportunityId(opportunity_id);
    }
  }, []);

  useEffect(() => {
    if (!interactionId) return;

    setSteps(INITIAL_STEPS);
    setIsComplete(false);
    setFinalStatus(null);

    const source = connectSSE(
      `/pipeline/progress/${interactionId}`,
      handleEvent,
      () => {},
      () => {},
    );
    sourceRef.current = source;

    return () => {
      source.close();
    };
  }, [interactionId, handleEvent]);

  return { steps, isComplete, finalStatus, opportunityId };
}
