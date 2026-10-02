import { describe, expect, it } from "vitest";
import { daysLeft, getStatus } from "./status";
import { makePromotion, NOW } from "./test-utils";

describe("getStatus", () => {
  it.each([
    [{}, "active"],
    [{ valid_from: "2026-10-03" }, "upcoming"],
    [{ valid_to: "2026-10-01" }, "expired"],
    [{ valid_to: "2026-10-02" }, "active"], // the last valid day still counts
    [{ valid_from: null, valid_to: null }, "active"],
    [{ is_active: false }, "expired"], // no longer seen by the scraper
  ] as const)("treats %o as %s", (overrides, expected) => {
    expect(getStatus(makePromotion(overrides), NOW)).toBe(expected);
  });

  it("uses Sri Lankan time to decide the current day", () => {
    // 20:00 UTC on 1 Oct is already 01:30 on 2 Oct in Colombo.
    const lateUtc = new Date("2026-10-01T20:00:00Z");
    expect(getStatus(makePromotion({ valid_to: "2026-10-01" }), lateUtc)).toBe("expired");
  });
});

describe("daysLeft", () => {
  it.each([
    ["2026-10-02", 0],
    ["2026-10-09", 7],
    ["2026-09-30", -2],
    [null, null],
  ] as const)("counts days until %s as %s", (validTo, expected) => {
    expect(daysLeft(makePromotion({ valid_to: validTo }), NOW)).toBe(expected);
  });
});
