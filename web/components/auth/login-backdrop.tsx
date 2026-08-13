"use client";

// Login backdrop — a full-bleed SVG with ~30 dots and faint connecting
// lines, low opacity, no animation. Static on purpose: the eye fills in
// the rest, and we honor prefers-reduced-motion by default.
//
// Deterministic placement uses a tiny inline PRNG so the dots don't
// shift between server-rendered HTML and the client-hydrated version
// (otherwise React would warn about hydration mismatches).

import * as React from "react";

// Mulberry32 — small, deterministic PRNG seeded by an integer.
function mulberry32(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = seed;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function LoginBackdrop() {
  const rand = React.useMemo(() => mulberry32(0x5ec12ec), []);
  // Stable across renders: layout is fixed, the canvas is pointer-events:none
  const dots = React.useMemo(() => {
    const out: { x: number; y: number; r: number }[] = [];
    for (let i = 0; i < 36; i++) {
      out.push({
        x: rand() * 100,
        y: rand() * 100,
        r: 0.4 + rand() * 0.9,
      });
    }
    return out;
  }, [rand]);

  // Pairs for the connecting lines — adjacent dots in the array.
  const lines = React.useMemo(() => {
    const out: { x1: number; y1: number; x2: number; y2: number }[] = [];
    for (let i = 0; i < dots.length - 1; i++) {
      const a = dots[i];
      const b = dots[i + 1];
      // Skip lines longer than 28% of the diagonal — keeps the constellation sparse.
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      if (Math.hypot(dx, dy) < 28) {
        out.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y });
      }
    }
    return out;
  }, [dots]);

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[var(--color-background)]"
    >
      {/* Soft radial gradient on top of the constellation, anchoring the eye to center. */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at center, color-mix(in oklch, var(--color-primary) 14%, transparent) 0%, transparent 60%)",
        }}
      />
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <g stroke="var(--color-primary)" strokeWidth="0.06" opacity="0.35">
          {lines.map((l, i) => (
            <line key={i} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} />
          ))}
        </g>
        <g fill="var(--color-foreground)" opacity="0.6">
          {dots.map((d, i) => (
            <circle key={i} cx={d.x} cy={d.y} r={d.r * 0.12} />
          ))}
        </g>
        {/* A few brighter "anchor" stars */}
        <g fill="var(--color-primary)" opacity="0.9">
          {dots.slice(0, 4).map((d, i) => (
            <circle key={`a-${i}`} cx={d.x} cy={d.y} r={d.r * 0.22} />
          ))}
        </g>
      </svg>
    </div>
  );
}