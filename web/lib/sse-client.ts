// Server-Sent Events parser targeted at our /api/chat endpoint.
//
// The contract is one event per line, event shapes:
//   event: meta\ndata: <json>\n\n
//   event: evidence\ndata: <json>\n\n
//   event: token\ndata: <json>\n\n
//   event: done\ndata: <json>\n\n
//   event: error\ndata: <json>\n\n
//
// We hand back a small discriminated union (`ChatEvent`) and let the
// caller route on `event` — keeps the parsing layer free of UI logic.

import type { ChatEvent } from "./types";

export class SSEError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SSEError";
  }
}

interface PendingEvent {
  event: string | null;
  data: string[];
}

function dispatch(pending: PendingEvent): ChatEvent | null {
  if (!pending.event || pending.data.length === 0) return null;
  const text = pending.data.join("\n");
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    // Malformed payload — surface as an error event so the caller can decide.
    return {
      event: "error",
      data: { message: "Malformed SSE payload", type: "DecodeError" },
    };
  }
  switch (pending.event) {
    case "meta":
    case "evidence":
    case "token":
    case "done":
    case "error":
      return { event: pending.event, data: parsed } as ChatEvent;
    default:
      return null; // unknown event name — ignore (forward-compatible)
  }
}

export async function* streamChat(
  query: string,
  signal?: AbortSignal,
  sessionId?: string,
): AsyncGenerator<ChatEvent> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/api/chat`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ query, session_id: sessionId }),
      signal,
    },
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new SSEError("Not authenticated");
    }
    throw new SSEError(`HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new SSEError("No response body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const pending: PendingEvent = { event: null, data: [] };

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    // sse-starlette emits lines terminated with CRLF (\r\n). The SSE
    // spec lets a server pick any of \r\n, \r, or \n as the line
    // terminator, and a frame is a *blank line* — two consecutive
    // terminators. Normalise every byte we read to LF before searching
    // for the frame boundary so all three wire variants parse the same.
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n?/g, "\n");
    let idx: number;
    // SSE frames are separated by a blank line (\n\n).
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      // Reset pending on each frame.
      pending.event = null;
      pending.data = [];
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) {
          pending.event = line.slice("event:".length).trim();
        } else if (line.startsWith("data:")) {
          pending.data.push(line.slice("data:".length).trimStart());
        }
      }
      const ev = dispatch(pending);
      if (ev) yield ev;
    }
  }
}
