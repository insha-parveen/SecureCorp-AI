// Unit tests for the data-driven primitives. Pure render-and-assert
// checks; no animations or interactions to drive here.

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Sparkline } from "@/components/ui/sparkline";

describe("Sparkline", () => {
  it("renders without crashing when given 2+ points", () => {
    const { container } = render(<Sparkline values={[1, 2, 3, 4]} />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    const path = svg?.querySelector("path");
    expect(path).not.toBeNull();
  });

  it("renders the trailing data-end as a 2px circle", () => {
    const { container } = render(<Sparkline values={[1, 2, 3, 4]} />);
    const dot = container.querySelector("circle");
    expect(dot?.getAttribute("r")).toBe("2");
  });

  it("renders nothing for empty input", () => {
    const { container } = render(<Sparkline values={[]} />);
    expect(container.querySelector("svg")).toBeNull();
  });

  it("renders nothing for a single point (no line possible)", () => {
    const { container } = render(<Sparkline values={[42]} />);
    expect(container.querySelector("svg")).toBeNull();
  });
});
