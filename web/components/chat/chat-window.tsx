// The chat window. Sticky input at the bottom, scrollable thread above.
// Sources panel appears whenever the latest assistant message has
// evidence — that's the "instant" rendering the plan calls for.

"use client";

import { useEffect, useRef, useState } from "react";
import { useStreamingChatContext } from "@/lib/streaming-chat-context";
import { MessageBubble } from "./message-bubble";
import { SuggestedQuestions } from "./suggested-questions";
import { SourcesPanel } from "@/components/chat/sources-panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ChatWindow() {
  // Consume the SHARED streaming state (same instance the pipeline reads),
  // so the pipeline animates in lockstep with the tokens rendered here.
  const { messages, isStreaming, submit } = useStreamingChatContext();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (isStreaming || !input.trim()) return;
    const query = input.trim();
    setInput("");
    void submit(query);
  };

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const sources =
    lastAssistant && lastAssistant.role === "assistant" ? lastAssistant.content.evidence : [];

  return (
    <div className="flex h-dvh flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-12">
              <h2 className="text-lg font-semibold">Ask anything about NexaCore policies</h2>
              <p className="text-sm text-[var(--color-muted-foreground)]">
                Or pick one of the prompts below to get started.
              </p>
              <SuggestedQuestions
                onSelect={(prompt) => {
                  setInput(prompt);
                }}
              />
            </div>
          ) : (
            messages.map((m, i) => <MessageBubble key={i} message={m} />)
          )}

          {sources.length > 0 ? (
            <div className="mt-2">
              <SourcesPanel evidence={sources} title="Sources" />
            </div>
          ) : null}
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 border-t border-[var(--color-border)] bg-[var(--color-background)]/80 px-4 py-3 backdrop-blur"
      >
        <div className="mx-auto flex max-w-2xl items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about NexaCore policies…"
            disabled={isStreaming}
            aria-label="Question"
          />
          <Button type="submit" disabled={isStreaming || !input.trim()}>
            {isStreaming ? "Streaming…" : "Send"}
          </Button>
        </div>
      </form>
    </div>
  );
}
