/**
 * SSE EventSource utility for connecting to backend SSE endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export function connectSSE(
  path: string,
  onEvent: (event: SSEEvent) => void,
  onComplete?: () => void,
  onError?: (error: Event) => void,
): EventSource {
  const url = `${API_BASE_URL}/api/v1${path}`;
  const source = new EventSource(url, { withCredentials: true });

  source.addEventListener("agent_progress", (e: MessageEvent) => {
    const data = JSON.parse(e.data);
    onEvent({ event: "agent_progress", data });
  });

  source.addEventListener("pipeline_complete", (e: MessageEvent) => {
    const data = JSON.parse(e.data);
    onEvent({ event: "pipeline_complete", data });
    source.close();
    onComplete?.();
  });

  source.onerror = (e) => {
    source.close();
    onError?.(e);
  };

  return source;
}
