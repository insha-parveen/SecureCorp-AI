// jsdom test setup. Loads testing-library's matchers and stubs out the
// fetch + TextDecoder/TextEncoder APIs jsdom doesn't ship.

import "@testing-library/jest-dom/vitest";

// jsdom provides TextEncoder; we add TextDecoder for the SSE parser tests.
import { TextDecoder } from "node:util";
if (typeof globalThis.TextDecoder === "undefined") {
  // @ts-expect-error: jsdom doesn't ship TextDecoder
  globalThis.TextDecoder = TextDecoder;
}