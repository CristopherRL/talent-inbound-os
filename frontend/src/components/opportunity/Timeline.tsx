"use client";

import { useState } from "react";
import StageBadge from "./StageBadge";

interface TimelineEvent {
  id: string;
  type: "interaction" | "transition";
  timestamp: string;
  // interaction fields
  source?: string;
  interaction_type?: string;
  raw_content?: string;
  // transition fields
  from_stage?: string;
  to_stage?: string;
  triggered_by?: string;
  is_unusual?: boolean;
  note?: string;
}

interface TimelineProps {
  events: TimelineEvent[];
}

function InteractionEvent({ event }: { event: TimelineEvent }) {
  const [expanded, setExpanded] = useState(false);
  const LINE_THRESHOLD = 120; // approximate chars for ~3 lines
  const isLong = (event.raw_content?.length ?? 0) > LINE_THRESHOLD;

  const isCandidateResponse = event.interaction_type === "CANDIDATE_RESPONSE";
  const dotColor = isCandidateResponse ? "bg-emerald-500" : "bg-primary";
  const labelColor = isCandidateResponse ? "text-emerald-400" : "text-primary";

  let label = "Recruiter: Initial message";
  if (isCandidateResponse) {
    label = "Your response (sent)";
  } else if (event.interaction_type === "FOLLOW_UP") {
    label = "Recruiter: Follow-up";
  }

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className={`w-2.5 h-2.5 rounded-full ${dotColor} mt-1.5`} />
        <div className="w-px flex-1 bg-border" />
      </div>
      <div className="pb-4 flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium ${labelColor}`}>
            {label}
          </span>
          {!isCandidateResponse && (
            <span className="text-xs text-muted-foreground">via {event.source}</span>
          )}
          <span className="text-xs text-muted-foreground">
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
        {event.raw_content && (
          <div className="mt-1">
            <p
              className={`text-xs text-foreground/70 whitespace-pre-wrap ${
                !expanded && isLong ? "line-clamp-3" : ""
              } ${expanded ? "max-h-48 overflow-y-auto" : ""}`}
            >
              {event.raw_content}
            </p>
            {isLong && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-primary hover:text-primary/80 mt-0.5 transition-colors"
              >
                {expanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TransitionEvent({ event }: { event: TimelineEvent }) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div
          className={`w-2.5 h-2.5 rounded-full mt-1.5 ${event.is_unusual ? "bg-amber-500" : "bg-muted-foreground/50"}`}
        />
        <div className="w-px flex-1 bg-border" />
      </div>
      <div className="pb-4 flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground">Stage changed</span>
          {event.from_stage && <StageBadge stage={event.from_stage} />}
          <span className="text-xs text-muted-foreground">&rarr;</span>
          {event.to_stage && <StageBadge stage={event.to_stage} />}
          <span className="text-xs text-muted-foreground">
            by {event.triggered_by}
          </span>
          {event.is_unusual && (
            <span className="text-xs text-amber-400 font-medium">
              (unusual)
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
        {event.note && (
          <p className="mt-1 text-xs text-muted-foreground italic">{event.note}</p>
        )}
      </div>
    </div>
  );
}

export default function Timeline({ events }: TimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No timeline events yet.</p>
    );
  }

  return (
    <div>
      {events.map((event) =>
        event.type === "interaction" ? (
          <InteractionEvent key={event.id} event={event} />
        ) : (
          <TransitionEvent key={event.id} event={event} />
        ),
      )}
    </div>
  );
}

export type { TimelineEvent };
