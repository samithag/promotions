import { describe, expect, it } from "vitest";
import { buildMockPromotions } from "./mock-data";
import { countCategories, queryPromotions } from "./mock-repository";
import { parsePromotionQuery } from "./query";
import { getStatus } from "./status";
import { makePromotion, NOW } from "./test-utils";

const query = (params: Record<string, string> = {}) =>
  parsePromotionQuery({ status: "all", ...params });

describe("queryPromotions", () => {
  const promotions = [
    makePromotion({ id: "a", bank: "combank", category: "dining", merchant: "Pizza Hut", first_seen_at: "2026-09-01T00:00:00Z", valid_to: "2026-10-20", discount_value: 20 }),
    makePromotion({ id: "b", bank: "sampath", category: "fuel", merchant: "Ceypetco", first_seen_at: "2026-09-20T00:00:00Z", valid_to: "2026-10-05", discount_type: "fixed", discount_value: 500 }),
    makePromotion({ id: "c", bank: "sampath", category: "dining", merchant: "Barista", first_seen_at: "2026-09-10T00:00:00Z", valid_to: null, discount_value: 50 }),
    makePromotion({ id: "d", bank: "combank", category: "travel", merchant: "SriLankan", first_seen_at: "2026-08-01T00:00:00Z", valid_to: "2026-09-30", discount_type: "installment", discount_value: 12 }),
  ];
  const ids = (params?: Record<string, string>) =>
    queryPromotions(promotions, query(params), NOW).items.map((p) => p.id);

  it.each([
    [{ bank: "sampath" }, ["b", "c"]],
    [{ category: "dining" }, ["a", "c"]],
    [{ bank: "combank", category: "dining" }, ["a"]],
  ])("filters by %o", (params, expected) => {
    expect(ids(params).sort()).toEqual(expected);
  });

  it("filters by derived status", () => {
    expect(ids({ status: "expired" })).toEqual(["d"]);
    expect(ids({ status: "active" }).sort()).toEqual(["a", "b", "c"]);
  });

  it("searches merchant, title and description case-insensitively", () => {
    const searchable = [
      makePromotion({ id: "m", merchant: "Barista" }),
      makePromotion({ id: "t", title: "Free barista coffee" }),
      makePromotion({ id: "d", description: "At any BARISTA café" }),
      makePromotion({ id: "x" }),
    ];
    const found = queryPromotions(searchable, query({ q: "barista" }), NOW).items;
    expect(found.map((p) => p.id).sort()).toEqual(["d", "m", "t"]);
  });

  it("sorts newest first by default", () => {
    expect(ids()).toEqual(["b", "c", "a", "d"]);
  });

  it("sorts by end date with open-ended offers last", () => {
    expect(ids({ sort: "ending_soon" })).toEqual(["d", "b", "a", "c"]);
  });

  it("sorts by discount: percentages, then fixed, then installments", () => {
    expect(ids({ sort: "discount" })).toEqual(["c", "a", "b", "d"]);
  });

  it("sorts offers without a discount after all others", () => {
    const withUnknown = [makePromotion({ id: "none", discount_type: null, discount_value: null }), ...promotions];
    const sorted = queryPromotions(withUnknown, query({ sort: "discount" }), NOW).items;
    expect(sorted.at(-1)?.id).toBe("none");
  });

  it("paginates and reports the total", () => {
    const page = queryPromotions(promotions, { ...query(), pageSize: 3, page: 2 }, NOW);
    expect(page).toMatchObject({ total: 4, page: 2, page_size: 3 });
    expect(page.items.map((p) => p.id)).toEqual(["d"]);
  });
});

describe("countCategories", () => {
  it("counts every category, including empty ones, for a status", () => {
    const promotions = [
      makePromotion({ category: "dining" }),
      makePromotion({ category: "dining", is_active: false }),
      makePromotion({ category: "fuel" }),
    ];
    const counts = countCategories(promotions, "active", NOW);
    expect(counts).toHaveLength(10);
    expect(counts.find((c) => c.slug === "dining")?.count).toBe(1);
    expect(counts.find((c) => c.slug === "fuel")?.count).toBe(1);
    expect(counts.find((c) => c.slug === "travel")?.count).toBe(0);
  });
});

describe("buildMockPromotions", () => {
  it("always contains active, upcoming and expired offers", () => {
    const statuses = new Set(buildMockPromotions(NOW).map((p) => getStatus(p, NOW)));
    expect(statuses).toEqual(new Set(["active", "upcoming", "expired"]));
  });
});
