"use client";

import { useState } from "react";
import StatusBadge from "./StatusBadge";

interface TimelineEvent {
  id: string;
  type: "interaction" | "transition";
  timestamp: string;
  // interaction fields
  source?: string;
  interaction_type?: string;
  raw_content?: string;
  // transition fields
  from_status?: string;
  to_status?: string;
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

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-2.5 h-2.5 rounded-full bg-blue-500 mt-1.5" />
        <div className="w-px flex-1 bg-gray-200" />
      </div>
      <div className="pb-4 flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-blue-600">
            {event.interaction_type === "FOLLOW_UP" ? "Follow-up" : "Initial message"}
          </span>
          <span className="text-xs text-gray-400">via {event.source}</span>
          <span className="text-xs text-gray-400">
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
        {event.raw_content && (
          <div className="mt-1">
            <p
              className={`text-xs text-gray-600 whitespace-pre-wrap ${
                !expanded && isLong ? "line-clamp-3" : ""
              } ${expanded ? "max-h-48 overflow-y-auto" : ""}`}
            >
              {event.raw_content}
            </p>
            {isLong && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-blue-500 hover:text-blue-700 mt-0.5"
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
          className={`w-2.5 h-2.5 rounded-full mt-1.5 ${event.is_unusual ? "bg-yellow-500" : "bg-gray-400"}`}
        />
        <div className="w-px flex-1 bg-gray-200" />
      </div>
      <div className="pb-4 flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-500">Status changed</span>
          {event.from_status && <StatusBadge status={event.from_status} />}
          <span className="text-xs text-gray-400">&rarr;</span>
          {event.to_status && <StatusBadge status={event.to_status} />}
          <span className="text-xs text-gray-400">
            by {event.triggered_by}
          </span>
          {event.is_unusual && (
            <span className="text-xs text-yellow-600 font-medium">
              (unusual)
            </span>
          )}
          <span className="text-xs text-gray-400">
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
        {event.note && (
          <p className="mt-1 text-xs text-gray-500 italic">{event.note}</p>
        )}
      </div>
    </div>
  );
}

export default function Timeline({ events }: TimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-gray-500">No timeline events yet.</p>
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
