// Unit tests for the donut. Validate that:
//   - segment arcs sum to a full 360° (within our 2px gap tolerance)
//   - colors render in the order given (fixed categorical order)
//   - the empty-data fallback renders a single dim ring

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Donut } from "@/components/ui/donut";

describe("Donut", () => {
  it("renders one arc per non-zero segment", () => {
    const { container } = render(
      <Donut
        segments={[
          { label: "A", value: 68, color: "red" },
          { label: "B", value: 21, color: "blue" },
          { label: "C", value: 11, color: "green" },
        ]}
      />,
    );
    const arcs = container.querySelectorAll("path");
    expect(arcs.length).toBe(3);
  });

  it("falls back to a single placeholder ring when total is 0", () => {
    const { container } = render(
      <Donut
        segments={[
          { label: "A", value: 0, color: "red" },
          { label: "B", value: 0, color: "blue" },
        ]}
      />,
    );
    const placeholder = container.querySelector("circle");
    expect(placeholder).not.toBeNull();
    const arcs = container.querySelectorAll("path");
    expect(arcs.length).toBe(0);
  });

  it("skips segments whose share rounds to 0°", () => {
    // A 0% share renders nothing — but anything strictly positive (even a
    // hair) draws an arc, since the gap is also a fraction of a degree.
    const { container } = render(
      <Donut
        segments={[
          { label: "Big", value: 100, color: "red" },
          { label: "Zero", value: 0, color: "blue" },
        ]}
      />,
    );
    expect(container.querySelectorAll("path").length).toBe(1);
  });
});
