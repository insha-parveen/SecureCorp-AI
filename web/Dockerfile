# web/Dockerfile — Next.js 15 standalone production image.
#
# Three stages: deps (install once, cached), builder (compile with the public
# API base baked in), runner (slim image carrying only the standalone server
# and static assets). The standalone output means node_modules is NOT copied
# wholesale — only Next's traced runtime deps ship.
FROM node:22-alpine AS deps

WORKDIR /app

# Reproducible install from the lockfile. npm ci is deterministic and fails
# if package.json and package-lock.json disagree (npm install would silently
# mutate the lock).
COPY package.json package-lock.json ./
RUN npm ci

# --- Build stage ---
FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* is inlined into the client bundle at build time, so the
# public backend URL MUST be present here — not at runtime. Railway passes
# service variables as build args; docker-compose passes it via `args`.
# Falls back to the dev origin so a bare `docker build` still produces a
# working local image.
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# --- Production stage ---
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Non-root runtime user.
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Standalone output: a minimal server bundle + only the traced deps.
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# The standalone server reads PORT from the environment; Railway injects it,
# local/compose defaults to 3000. HOSTNAME=0.0.0.0 makes it bind all
# interfaces inside the container.
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
CMD ["node", "server.js"]
