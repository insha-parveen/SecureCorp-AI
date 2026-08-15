"use client";

// StreamingChatProvider — owns a SINGLE useStreamingChat instance and
// shares it with every descendant (the chat window AND the pipeline
// visualization).
//
// Why this exists: before this provider, ChatWindow called
// useStreamingChat(sessionId) and PipelinePanel called useStreamingChat()
// independently. Each call is its own React state machine, so the
// pipeline's `isStreaming` was ALWAYS false — the pipeline never animated
// during a real chat. Lifting the hook into one context is the fix: the
// chat and the pipeline now read the exact same streaming state, so the
// pipeline animates in lockstep with the tokens the user sees.

import * as React from "react";
import { useStreamingChat } from "@/hooks/use-streaming-chat";
import type { Message } from "@/lib/types";

export interface StreamingChatValue {
  messages: Message[];
  isStreaming: boolean;
  submit: (query: string) => Promise<void>;
  reset: () => void;
}

const StreamingChatContext = React.createContext<StreamingChatValue | null>(null);

export function StreamingChatProvider({ children }: { children: React.ReactNode }) {
  // One stable session ID for the life of the provider (per browser tab /
  // chat surface). This is what threads conversation history server-side.
  const [sessionId] = React.useState(() => crypto.randomUUID());
  const value = useStreamingChat(sessionId);
  return (
    <StreamingChatContext.Provider value={value}>{children}</StreamingChatContext.Provider>
  );
}

/**
 * Read the shared streaming-chat state. Must be called inside a
 * <StreamingChatProvider>. Throwing (rather than returning null) keeps the
 * "pipeline silently never animates" class of bug from ever recurring — a
 * missing provider fails loudly instead.
 */
export function useStreamingChatContext(): StreamingChatValue {
  const ctx = React.useContext(StreamingChatContext);
  if (ctx === null) {
    throw new Error("useStreamingChatContext must be used within a <StreamingChatProvider>");
  }
  return ctx;
}
