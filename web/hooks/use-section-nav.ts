"use client";

// use-section-nav — scroll-spy for the landing page's sticky section nav.
// Given the ordered list of section ids, it returns the id currently in
// view and a `go(id)` that smooth-scrolls to a section (respecting
// prefers-reduced-motion). Pure IntersectionObserver, no scroll listener,
// so it stays cheap and never fights the browser's own scrolling.

import * as React from "react";

export function useSectionNav(sectionIds: string[]) {
  const [active, setActive] = React.useState<string>(sectionIds[0] ?? "");

  React.useEffect(() => {
    if (typeof window === "undefined" || sectionIds.length === 0) return;

    const elements = sectionIds
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);
    if (elements.length === 0) return;

    // Track intersection ratios per id; the most-visible section wins. The
    // rootMargin biases toward a section once it crosses the upper third,
    // which matches how people read a long page top-down.
    const ratios = new Map<string, number>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          ratios.set(entry.target.id, entry.isIntersecting ? entry.intersectionRatio : 0);
        }
        let best = "";
        let bestRatio = 0;
        for (const [id, ratio] of ratios) {
          if (ratio > bestRatio) {
            bestRatio = ratio;
            best = id;
          }
        }
        if (best) setActive(best);
      },
      {
        rootMargin: "-30% 0px -55% 0px",
        threshold: [0, 0.25, 0.5, 0.75, 1],
      },
    );

    for (const el of elements) observer.observe(el);
    return () => observer.disconnect();
  }, [sectionIds]);

  const go = React.useCallback((id: string) => {
    if (typeof window === "undefined") return;
    const el = document.getElementById(id);
    if (!el) return;
    const prefersReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    el.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "start" });
    // Move focus for keyboard users without yanking the viewport a second time.
    el.setAttribute("tabindex", "-1");
    (el as HTMLElement).focus({ preventScroll: true });
  }, []);

  return { active, go };
}
