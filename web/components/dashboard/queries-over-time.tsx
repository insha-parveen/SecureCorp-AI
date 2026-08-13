"use client";

// QueriesOverTime — single-series line chart of total queries per
// weekday over the last 7 days. Hand-rolled inline SVG.
//
// Per the data-viz skill rules in this skill bundle:
//   - single series → no legend (the title names it)
//   - 2px stroke, 4px rounded data-end anchored to the baseline
//   - recessive grid + axes (text in muted token, never series color)
//   - direct-label the latest point so the eye lands on the headline
//   - hover layer with a crosshair + tooltip (default for any line)

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { getQueriesOverTime } from "@/lib/api";
import { queriesOverTime as mockQueriesOverTime } from "@/lib/mock-data";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

const W = 480;
const H = 180;
const PAD_X = 28;
const PAD_TOP = 16;
const PAD_BOTTOM = 28;

export function QueriesOverTime() {
  // Fetch real data; fall back to demo data when the DB has no logs yet.
  const { data: fetched } = useQuery({
    queryKey: ["queries-over-time"],
    queryFn: getQueriesOverTime,
  });
  const isLive = Boolean(fetched && fetched.length > 0);
  const data = isLive ? fetched! : mockQueriesOverTime;
  const values = data.map((d) => d.value);
  const max = Math.max(...values);
  const min = 0;
  const range = max - min || 1;

  const innerW = W - PAD_X * 2;
  const innerH = H - PAD_TOP - PAD_BOTTOM;
  const step = innerW / (data.length - 1);

  const points = data.map((d, i) => {
    const x = PAD_X + i * step;
    const y = PAD_TOP + innerH * (1 - (d.value - min) / range);
    return { x, y, ...d };
  });

  const linePath = points
    .map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
    .join(" ");

  const areaPath =
    `M ${points[0].x} ${PAD_TOP + innerH} ` +
    points.map((p) => `L ${p.x} ${p.y}`).join(" ") +
    ` L ${points[points.length - 1].x} ${PAD_TOP + innerH} Z`;

  // Y-axis ticks at 0, mid, max — recessive text.
  const ticks = [0, Math.round(max / 2), max];

  // Hover state — index of nearest point.
  const [hover, setHover] = React.useState<number | null>(null);

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const target = e.currentTarget;
    const rect = target.getBoundingClientRect();
    const xPct = (e.clientX - rect.left) / rect.width;
    const xCoord = xPct * W;
    let nearest = 0;
    let nearestDist = Infinity;
    for (let i = 0; i < points.length; i++) {
      const dist = Math.abs(points[i].x - xCoord);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = i;
      }
    }
    setHover(nearest);
  }

  const latest = points[points.length - 1];

  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex flex-col gap-1">
          <GlassCardTitle>Queries over time</GlassCardTitle>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Total queries per weekday (last 7 days)
          </p>
        </div>
        <Badge variant="muted">{isLive ? "Live" : "(Demo data)"}</Badge>
      </GlassCardHeader>
      <GlassCardContent>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="block h-auto w-full"
          role="img"
          aria-label={`Line chart of total queries per weekday. Most recent: ${latest.value}.`}
          onMouseMove={handleMove}
          onMouseLeave={() => setHover(null)}
        >
          <defs>
            <linearGradient id="qot-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="var(--color-primary)" stopOpacity="0.25" />
              <stop offset="1" stopColor="var(--color-primary)" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Y-axis tick lines + labels */}
          {ticks.map((t) => {
            const y = PAD_TOP + innerH * (1 - (t - min) / range);
            return (
              <g key={t}>
                <line
                  x1={PAD_X}
                  x2={W - PAD_X}
                  y1={y}
                  y2={y}
                  stroke="var(--color-border)"
                  strokeWidth="0.5"
                  opacity="0.5"
                />
                <text
                  x={PAD_X - 6}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="9"
                  fill="var(--color-muted-foreground)"
                >
                  {t}
                </text>
              </g>
            );
          })}

          {/* X-axis labels */}
          {points.map((p, i) => (
            <text
              key={i}
              x={p.x}
              y={H - PAD_BOTTOM + 14}
              textAnchor="middle"
              fontSize="9"
              fill="var(--color-muted-foreground)"
            >
              {p.label}
            </text>
          ))}

          {/* Area + line */}
          <path d={areaPath} fill="url(#qot-area)" />
          <path
            d={linePath}
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points + hover crosshair */}
          {points.map((p, i) => (
            <g key={i}>
              {hover === i ? (
                <line
                  x1={p.x}
                  x2={p.x}
                  y1={PAD_TOP}
                  y2={PAD_TOP + innerH}
                  stroke="var(--color-border)"
                  strokeWidth="1"
                />
              ) : null}
              <circle
                cx={p.x}
                cy={p.y}
                r={hover === i ? 4 : 3}
                fill="var(--color-background)"
                stroke="var(--color-primary)"
                strokeWidth="2"
              />
            </g>
          ))}

          {/* Direct-label the latest data-end so the headline number lives
              on the chart itself (per the data-viz skill: selective direct
              labels, never a number on every point). */}
          <text
            x={latest.x - 6}
            y={latest.y - 8}
            textAnchor="end"
            fontSize="10"
            fontWeight="600"
            fill="var(--color-foreground)"
          >
            {latest.value}
          </text>
        </svg>

        {/* Hover tooltip — sits below the chart so it doesn't overlap marks */}
        {hover !== null ? (
          <div
            className="mt-2 flex items-center justify-between rounded-md border border-[var(--color-border)] bg-[var(--color-card)]/70 px-3 py-1.5 text-xs"
            aria-live="polite"
          >
            <span className="font-medium">{points[hover].label}</span>
            <span className="tabular-nums text-[var(--color-muted-foreground)]">
              {points[hover].value} queries
            </span>
          </div>
        ) : null}
      </GlassCardContent>
    </GlassCard>
  );
}