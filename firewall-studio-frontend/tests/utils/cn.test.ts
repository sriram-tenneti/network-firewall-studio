import { describe, expect, it } from "vitest";
import { cn } from "../../src/lib/utils";

describe("cn (tailwind class merger)", () => {
  it("joins string classes", () => {
    expect(cn("a", "b")).toContain("a");
    expect(cn("a", "b")).toContain("b");
  });

  it("skips falsy values", () => {
    const out = cn("a", false && "b", null, undefined, "c");
    expect(out).toContain("a");
    expect(out).toContain("c");
    expect(out).not.toContain("b");
  });

  it("dedups conflicting tailwind classes (last wins)", () => {
    const out = cn("p-2", "p-4");
    expect(out).toContain("p-4");
    expect(out).not.toContain("p-2");
  });

  it("handles object form", () => {
    const out = cn({ "a": true, "b": false, "c": true });
    expect(out).toContain("a");
    expect(out).toContain("c");
    expect(out).not.toContain("b");
  });
});
