import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The Next.js app talks to FastAPI at http://localhost:8000 in dev.
  // In production they share an origin or sit behind a proxy that injects
  // the same path, so no rewrite is needed there.
  reactStrictMode: true,
  experimental: {
    // Keep the dev experience snappy. The chat route does SSE; we want fast
    // page transitions but we don't enable PPR (partial prerendering) for MVP.
  },
};

export default nextConfig;