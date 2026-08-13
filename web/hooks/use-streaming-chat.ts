"use client";

// Wraps the SSE stream from `/api/chat` into a React-friendly state
// machine. The hook:
//   1. Starts an AbortController when the user submits a query.
//   2. Accumulates `evidence` events into the assistant message.
//   3. Concatenates `token` events into the streaming text.
//   4. Stops on `done` and stores the validated payload.
//   5. Stops on `error` and stores a typed error so the UI can render a
//      card instead of a silent broken state.

import { useCallback, useState } from "react";
import { streamChat } from "@/lib/sse-client";
import type { AssistantMessage, Message, RankedEvidence } from "@/lib/types";

const EMPTY_ASSISTANT: AssistantMessage = {
  meta: null,
  evidence: [],
  text: "",
  done: null,
  error: null,
};

export function useStreamingChat(sessionId?: string): {
  messages: Message[];
  isStreaming: boolean;
  submit: (query: string) => Promise<void>;
  reset: () => void;
} {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const submit = useCallback(async (query: string) => {
    if (!query.trim()) return;

    // Optimistic user message; the assistant message is created in the
    // pending state so the UI can render a caret immediately.
    setMessages((prev) => [
      ...prev,
      { role: "user", content: { text: query } },
      { role: "assistant", content: { ...EMPTY_ASSISTANT } },
    ]);
    setIsStreaming(true);

    const controller = new AbortController();
    const evidenceAcc: RankedEvidence[] = [];

    try {
      for await (const ev of streamChat(query, controller.signal, sessionId)) {
        setMessages((prev) => {
          const next = prev.slice();
          const idx = next.length - 1;
          if (idx < 0 || next[idx].role !== "assistant") return prev;
          const current = next[idx].content;
          const updated: AssistantMessage = { ...current };
          switch (ev.event) {
            case "meta":
              updated.meta = ev.data;
              break;
            case "evidence":
              evidenceAcc.push(ev.data);
              updated.evidence = evidenceAcc.slice();
              break;
            case "token":
              updated.text = current.text + ev.data.text;
              break;
            case "done":
              updated.done = ev.data;
              break;
            case "error":
              updated.error = ev.data;
              break;
          }
          next[idx] = { role: "assistant", content: updated };
          return next;
        });
      }
    } catch (err) {
      setMessages((prev) => {
        const next = prev.slice();
        const idx = next.length - 1;
        if (idx < 0 || next[idx].role !== "assistant") return prev;
        const updated: AssistantMessage = {
          ...next[idx].content,
          error: {
            message: err instanceof Error ? err.message : "Stream failed",
            type: "StreamError",
          },
        };
        next[idx] = { role: "assistant", content: updated };
        return next;
      });
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setIsStreaming(false);
  }, []);

  return { messages, isStreaming, submit, reset };
}
