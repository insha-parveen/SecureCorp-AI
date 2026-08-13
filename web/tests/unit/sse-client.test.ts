// Unit test: the SSE parser correctly extracts all 4 event types and
// accumulates partial frames across chunk boundaries.

import { describe, expect, it, vi } from "vitest";
import { streamChat } from "@/lib/sse-client";

function makeResponse(chunks: Uint8Array[], final: boolean = true): Response {
  let i = 0;
  return {
    ok: true,
    status: 200,
    body: {
      getReader() {
        return {
          async read() {
            if (i >= chunks.length) return { value: undefined, done: true };
            const value = chunks[i++];
            return { value, done: false };
          },
          releaseLock() {},
        };
      },
    },
  } as unknown as Response;
}

describe("streamChat", () => {
  it("extracts meta, evidence, token, done events from a single chunk", async () => {
    const frame = [
      "event: meta",
      'data: {"route":"DOCUMENT_RAG","cache_tier":"MISS"}',
      "",
      "event: evidence",
      'data: {"rank":1,"chunk_id":"HR-001:v1:0001","document_id":"HR-001","document_title":"HR-001","section_title":null,"excerpt":"hi"}',
      "",
      "event: token",
      'data: {"text":"hello "}',
      "",
      "event: done",
      'data: {"answer":"hello","citations":[1],"evidence":[],"model":"llama3","usage":{},"extras":{}}',
      "",
      "",
    ].join("\n");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => makeResponse([new TextEncoder().encode(frame)])),
    );

    const events: Array<{ event: string }> = [];
    for await (const ev of streamChat("q")) events.push(ev as { event: string });

    expect(events.map((e) => e.event)).toEqual(["meta", "evidence", "token", "done"]);
  });

  it("handles frames split across multiple chunks", async () => {
    const part1 = new TextEncoder().encode("event: token\ndata: {\"te");
    const part2 = new TextEncoder().encode("xt\":\"a\"}\n\nevent: done\ndata: ");
    const part3 = new TextEncoder().encode('{"answer":"a","citations":[],"evidence":[],"model":"x","usage":{},"extras":{}}\n\n');
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => makeResponse([part1, part2, part3])),
    );

    const events: Array<{ event: string }> = [];
    for await (const ev of streamChat("q")) events.push(ev as { event: string });

    expect(events.map((e) => e.event)).toEqual(["token", "done"]);
  });

  it("handles CRLF line endings (sse-starlette's actual wire format)", async () => {
    // sse-starlette emits lines with \r\n terminators and a \r\n\r\n
    // frame separator. A naive parser that only looks for \n\n will
    // never find the frame boundary and the entire response will be
    // discarded. Regression: this caused the chat UI to stick on
    // "Thinking…" forever.
    const frame = [
      "event: done",
      'data: {"answer":"hi","citations":[],"evidence":[],"model":"x","usage":{},"extras":{}}',
      "",
      "",
    ].join("\r\n");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => makeResponse([new TextEncoder().encode(frame)])),
    );

    const events: Array<{ event: string }> = [];
    for await (const ev of streamChat("q")) events.push(ev as { event: string });

    expect(events.map((e) => e.event)).toEqual(["done"]);
  });

  it("handles mixed CRLF + LF across chunk boundaries", async () => {
    // Some chunks end mid-frame with \r\n, others with just \n. The
    // parser must accept both.
    const part1 = new TextEncoder().encode("event: done\r\ndata: {\"an");
    const part2 = new TextEncoder().encode('swer":"a","citations":[],"evidence":[],"model":"x","usage":{},"extras":{}}\n\n');
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => makeResponse([part1, part2])),
    );

    const events: Array<{ event: string }> = [];
    for await (const ev of streamChat("q")) events.push(ev as { event: string });

    expect(events.map((e) => e.event)).toEqual(["done"]);
  });

  it("throws SSEError on 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 401 }) as unknown as Response),
    );
    await expect(async () => {
      for await (const _ of streamChat("q")) {
        /* unreachable */
      }
    }).rejects.toThrow(/authenticated/i);
  });
});