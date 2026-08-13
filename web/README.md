# NexaCore AI — Web Client

The Next.js 15 frontend for SecureCorp AI. Sits next to `src/hybridrag/` as
a sibling ecosystem (separate package manager, separate deploy).

## Stack

- **Next.js 15** App Router + **React 19**
- **Tailwind v4** + shadcn/ui (Radix primitives — keyboard + screen reader done)
- **AI SDK 5** (`@ai-sdk/react`) — but the chat route is a custom SSE
  transport that targets our own `/api/chat`, not the AI SDK's hosted
  providers. Tokens are streamed via Server-Sent Events from FastAPI.
- **TanStack Query** — `/api/auth/me` + non-streaming fetches
- **Motion** (formerly Framer Motion) — three animations only:
  message enter (200ms), citation hover card (120/80ms), route crossfade (150ms).
  `prefers-reduced-motion` is honored at the CSS layer.

## Layout

```text
web/
├── app/                      Next.js App Router
│   ├── page.tsx              /  → redirect to /chat or /login
│   ├── login/page.tsx        /login — demo-user picker
│   ├── chat/                 /chat — the streaming surface
│   ├── layout.tsx            Inter+Tailwind, dark default
│   └── globals.css           Tailwind v4 + design tokens
├── components/
│   ├── auth/                 login-form, role-badge
│   ├── chat/                 chat-window, message-bubble, streaming-answer,
│   │                         citation-chip, citation-hover-card, suggested-questions
│   ├── layout/               app-shell, top-bar
│   ├── ui/                   shadcn primitives (button, card, input)
│   └── providers.tsx         TanStack Query + Auth context
├── lib/                      api, sse-client, types, utils, auth-context
├── hooks/use-streaming-chat.ts
├── tests/unit/               Vitest (SSE parser + hook)
└── tests/e2e/                Playwright (login + ask + cite)
```

## How auth works

1. User picks a demo user on `/login`.
2. `POST /api/auth/token` sets an httpOnly cookie (`sc_auth=...`).
3. Subsequent requests carry the cookie automatically (`credentials: 'include'`).
4. The frontend NEVER reads the token — `UserContext` is built server-side
   from the verified JWT.

This matches CLAUDE.md §5: server-validated identity, never trust the client.

## How streaming works

1. User submits a question in `chat-window`.
2. `useStreamingChat()` calls `streamChat(query, signal)` which is a
   generator over `fetch`'s body reader.
3. Three SSE event shapes: `evidence` (per chunk, before tokens),
   `token` (incremental text), `done` (the validated `FinalResponse`).
4. Tokens append to a streaming text. The done event freezes citations
   and replaces the caret with the final answer.

The `format: json_object` instruction is dropped on the streaming path —
the model emits prose, and we attempt one JSON parse at the end. A parse
failure yields raw text + empty citations (graceful fallback).

## Local dev

```bash
# Terminal 1 — backend
cd ..                                  # back to repo root
uv run uvicorn hybridrag.api.app:app --reload --port 8000

# Terminal 2 — frontend
pnpm install
pnpm dev                               # http://localhost:3000
```

The frontend talks to `http://localhost:8000` via `NEXT_PUBLIC_API_BASE`.
For a different origin, set it in `.env.local`.

## Tests

```bash
pnpm test            # Vitest unit tests (sse-client, useStreamingChat)
pnpm typecheck       # tsc --noEmit
pnpm lint            # next lint
pnpm test:e2e        # Playwright (requires dev server + backend)
```