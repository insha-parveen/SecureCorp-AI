// Unit tests for the gauge. Validate the math:
//   - the labelled percentage is the clamped value scaled to 100
//   - the value arc renders with the right width when the metric is
//     highlighted vs not
//   - aria-label carries the label + percentage for SR users

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Gauge } from "@/components/ui/gauge";

describe("Gauge", () => {
  it("renders the correct percentage from a 0..1 value", () => {
    const { container } = render(<Gauge value={0.91} label="Faithfulness" />);
    // The inner number is in a <span> with text "91" — matches 0.91 * 100.
    expect(container.textContent).toContain("91");
    expect(container.textContent).toContain("Faithfulness");
  });

  it("clamps values above max back into [0, max]", () => {
    const { container } = render(<Gauge value={1.4} max={1} label="Overflow" />);
    // 1.4 clamped to 1.0 → "100"
    expect(container.textContent).toContain("100");
  });

  it("emits an aria-label for screen readers", () => {
    const { container } = render(<Gauge value={0.5} label="Answer Relevancy" />);
    const el = container.querySelector('[role="img"]');
    expect(el?.getAttribute("aria-label")).toBe("Answer Relevancy: 50 percent");
  });

  it("renders with a thicker value ring when highlighted", () => {
    const { container, rerender } = render(
      <Gauge value={0.5} label="Faithfulness" highlighted={false} />,
    );
    const regularStrokeWidth = container.querySelectorAll("path")[1]?.getAttribute("stroke-width");

    rerender(<Gauge value={0.5} label="Faithfulness" highlighted={true} />);
    const highlightedStrokeWidth = container.querySelectorAll("path")[1]?.getAttribute("stroke-width");

    expect(Number(highlightedStrokeWidth)).toBeGreaterThan(Number(regularStrokeWidth));
  });
});
