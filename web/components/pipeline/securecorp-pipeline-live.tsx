"use client";

// SecureCorpPipelineLive — binds the SecureCorpPipeline to the live
// request lifecycle. Reads the SHARED streaming context (the same instance
// the chat window uses, so it animates in lockstep) and the JWT-verified
// current user (for the auth/authz detail rows).
//
// This is the /chat placement. The landing page mounts <SecureCorpPipeline>
// directly with a static/example message for the architecture showcase.

import * as React from "react";
import { useStreamingChatContext } from "@/lib/streaming-chat-context";
import { useCurrentUser } from "@/lib/auth-context";
import { SecureCorpPipeline } from "./securecorp-pipeline";
import type { AssistantMessage } from "@/lib/types";

export function SecureCorpPipelineLive({ className }: { className?: string }) {
  const { messages, isStreaming } = useStreamingChatContext();
  const { user } = useCurrentUser();

  // The latest assistant message drives the pipeline.
  const latest = React.useMemo<AssistantMessage | null>(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === "assistant") return m.content;
    }
    return null;
  }, [messages]);

  return (
    <SecureCorpPipeline
      message={latest}
      isStreaming={isStreaming}
      user={user}
      className={className}
    />
  );
}
