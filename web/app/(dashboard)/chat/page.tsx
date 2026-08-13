"use client";

// /chat — the authenticated HOME surface. Post-login lands here.
//
// This is the chat body only: <StreamingChatProvider> owns the single
// streaming instance both columns read, so the live pipeline animates in
// lockstep with the chat tokens. Auth gating, the top navigation, and the
// TanStack Query / AuthContext providers all come from the (dashboard) group
// layout — this page no longer wraps its own <Providers>/<AppShell>/gate.
//
// On md and below the pipeline drops below the chat.

import { ChatWindow } from "@/components/chat/chat-window";
import { SecureCorpPipelineLive } from "@/components/pipeline/securecorp-pipeline-live";
import { StreamingChatProvider } from "@/lib/streaming-chat-context";

export default function ChatPage() {
  return (
    <StreamingChatProvider>
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 md:grid-cols-[1fr_320px]">
        <ChatWindow />
        <div className="md:sticky md:top-20 md:self-start">
          <SecureCorpPipelineLive />
        </div>
      </div>
    </StreamingChatProvider>
  );
}
