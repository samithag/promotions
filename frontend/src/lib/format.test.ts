import { describe, expect, it } from "vitest";
import { formatDateRange, formatDiscount, formatValidity, isEndingSoon } from "./format";
import { makePromotion, NOW } from "./promotions/test-utils";

describe("formatDiscount", () => {
  it.each([
    [{ discount_type: "percentage", discount_value: 20 }, { figure: "20%", caption: "off" }],
    [{ discount_type: "fixed", discount_value: 2500 }, { figure: "Rs 2,500", caption: "off" }],
    [{ discount_type: "installment", discount_value: 24 }, { figure: "0%", caption: "for 24 months" }],
    [{ discount_type: null, discount_value: null }, { figure: "Deal", caption: "see details" }],
  ] as const)("formats %o", (overrides, expected) => {
    expect(formatDiscount(makePromotion(overrides))).toEqual(expected);
  });
});

describe("formatValidity", () => {
  it.each([
    [{}, "Until 31 Oct 2026"],
    [{ valid_to: "2026-10-02" }, "Ends today"],
    [{ valid_to: "2026-10-03" }, "Ends tomorrow"],
    [{ valid_to: "2026-10-07" }, "Ends in 5 days"],
    [{ valid_to: null }, "No end date"],
    [{ valid_from: "2026-11-01" }, "Starts 1 Nov 2026"],
    [{ valid_to: "2026-09-30" }, "Ended 30 Sept 2026"],
  ] as const)("describes %o as %s", (overrides, expected) => {
    expect(formatValidity(makePromotion(overrides), NOW)).toBe(expected);
  });
});

describe("isEndingSoon", () => {
  it("flags active offers ending within a week", () => {
    expect(isEndingSoon(makePromotion({ valid_to: "2026-10-09" }), NOW)).toBe(true);
    expect(isEndingSoon(makePromotion({ valid_to: "2026-10-10" }), NOW)).toBe(false);
    expect(isEndingSoon(makePromotion({ valid_to: "2026-09-30" }), NOW)).toBe(false);
  });

  it("never flags open-ended offers", () => {
    expect(isEndingSoon(makePromotion({ valid_to: null }), NOW)).toBe(false);
  });
});

describe("formatDateRange", () => {
  it.each([
    [{}, "1 Sept 2026 to 31 Oct 2026"],
    [{ valid_from: null }, "Until 31 Oct 2026"],
    [{ valid_to: null }, "From 1 Sept 2026, no end date"],
    [{ valid_from: null, valid_to: null }, "No dates given"],
  ] as const)("describes %o as %s", (overrides, expected) => {
    expect(formatDateRange(makePromotion(overrides))).toBe(expected);
  });
});
