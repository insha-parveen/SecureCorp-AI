// Unit test: the streaming hook appends token events, finalizes on done,
// and stores typed errors when the stream fails.

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useStreamingChat } from "@/hooks/use-streaming-chat";
import type { ChatEvent } from "@/lib/types";

// `vi.mock` is hoisted above the imports, so the hook module binds to this
// mock's `streamChat` the first time it is evaluated. Keeping the mock fn in
// `vi.hoisted` lets us swap its implementation per test. (A non-hoisted
// `vi.doMock` after the static `useStreamingChat` import above would be too
// late — the hook would already hold the real `streamChat`.)
const { streamChatMock } = vi.hoisted(() => ({ streamChatMock: vi.fn() }));
vi.mock("@/lib/sse-client", () => ({ streamChat: streamChatMock }));

function makeStream(events: ChatEvent[]): AsyncIterable<ChatEvent> {
  return {
    [Symbol.asyncIterator]() {
      let i = 0;
      return {
        async next() {
          if (i >= events.length) return { value: undefined, done: true } as const;
          const ev = events[i++];
          return { value: ev, done: false } as const;
        },
      };
    },
  };
}

beforeEach(() => {
  streamChatMock.mockReset();
});

describe("useStreamingChat", () => {
  it("accumulates tokens and stores the done payload", async () => {
    streamChatMock.mockReturnValue(
      makeStream([
        { event: "meta", data: { route: "DOCUMENT_RAG", cache_tier: "MISS" } },
        {
          event: "evidence",
          data: {
            rank: 1,
            chunk_id: "x",
            document_id: "X",
            document_title: "X",
            section_title: null,
            excerpt: "x",
          },
        },
        { event: "token", data: { text: "hello " } },
        { event: "token", data: { text: "world" } },
        {
          event: "done",
          data: {
            answer: "hello world",
            citations: [1],
            evidence: [],
            model: "llama3",
            usage: {},
            extras: {},
          },
        },
      ]),
    );

    const { result } = renderHook(() => useStreamingChat());

    await act(async () => {
      await result.current.submit("hi");
    });

    expect(result.current.messages.length).toBe(2);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[1].role).toBe("assistant");
    if (result.current.messages[1].role === "assistant") {
      expect(result.current.messages[1].content.text).toBe("hello world");
      expect(result.current.messages[1].content.done?.answer).toBe("hello world");
      expect(result.current.messages[1].content.evidence.length).toBe(1);
      expect(result.current.messages[1].content.meta?.route).toBe("DOCUMENT_RAG");
      expect(result.current.messages[1].content.meta?.cache_tier).toBe("MISS");
    }
    expect(result.current.isStreaming).toBe(false);
  });

  it("records a typed error when the stream throws", async () => {
    streamChatMock.mockImplementation(() => {
      throw new Error("boom");
    });

    const { result } = renderHook(() => useStreamingChat());
    await act(async () => {
      await result.current.submit("hi");
    });

    const last = result.current.messages[result.current.messages.length - 1];
    expect(last?.role).toBe("assistant");
    if (last?.role === "assistant") {
      expect(last.content.error?.message).toBe("boom");
    }
  });
});
