import { describe, expect, it } from "vitest";
import { PRODUCT_NAME, PRODUCT_SUBTITLE } from "../brand";
import { suggestForMood } from "../mood";

describe("brand", () => {
  it("exposes the product name and subtitle", () => {
    expect(PRODUCT_NAME).toBe("NEUROLEARN");
    expect(PRODUCT_SUBTITLE).toContain("adaptive learning");
  });
});

describe("mood mapping", () => {
  it("routes low-mood suggestions to crisis-safe copy", () => {
    expect(suggestForMood("Try box breathing… counselling services")).toContain("breathing");
  });
  it("routes break nudges", () => {
    expect(suggestForMood("a five-minute break could reset")).toContain("break");
  });
});
