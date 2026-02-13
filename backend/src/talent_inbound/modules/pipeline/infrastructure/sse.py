"""SSE event emitter — async queue per interaction for real-time progress."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any


class SSEEmitter:
    """Manages per-interaction async queues for Server-Sent Events.

    Each interaction_id gets its own asyncio.Queue. The pipeline writes
    events to the queue, and the SSE endpoint reads from it.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue] = {}

    def get_queue(self, interaction_id: str) -> asyncio.Queue:
        """Get or create the event queue for an interaction."""
        if interaction_id not in self._queues:
            self._queues[interaction_id] = asyncio.Queue()
        return self._queues[interaction_id]

    async def emit_progress(
        self,
        interaction_id: str,
        agent: str,
        status: str,
        result_summary: str = "",
    ) -> None:
        """Emit an agent_progress event."""
        queue = self.get_queue(interaction_id)
        event = {
            "event": "agent_progress",
            "data": {
                "agent": agent,
                "status": status,
                "result_summary": result_summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        await queue.put(event)

    async def emit_complete(
        self,
        interaction_id: str,
        opportunity_id: str,
        final_status: str,
    ) -> None:
        """Emit a pipeline_complete event and signal end of stream."""
        queue = self.get_queue(interaction_id)
        event = {
            "event": "pipeline_complete",
            "data": {
                "opportunity_id": opportunity_id,
                "final_status": final_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        await queue.put(event)
        # Sentinel to signal the SSE endpoint to close the stream
        await queue.put(None)

    async def stream(self, interaction_id: str):
        """Async generator that yields SSE-formatted strings."""
        queue = self.get_queue(interaction_id)
        while True:
            event = await queue.get()
            if event is None:
                break
            event_type = event["event"]
            data = json.dumps(event["data"])
            yield f"event: {event_type}\ndata: {data}\n\n"

        # Cleanup
        self._queues.pop(interaction_id, None)
