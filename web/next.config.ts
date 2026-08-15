import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle (.next/standalone/server.js) so the
  // production Docker image ships only the traced runtime deps instead of the
  // full 582M node_modules. The standalone server reads process.env.PORT,
  // which is what lets Railway's injected $PORT work without extra wiring.
  output: "standalone",
  // The Next.js app talks to FastAPI at http://localhost:8000 in dev.
  // In production the public backend URL is injected at build time via the
  // NEXT_PUBLIC_API_BASE build arg (see web/Dockerfile).
  reactStrictMode: true,
  experimental: {
    // Keep the dev experience snappy. The chat route does SSE; we want fast
    // page transitions but we don't enable PPR (partial prerendering) for MVP.
  },
};

export default nextConfig;