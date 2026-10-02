import { describe, expect, it } from "vitest";
import { MAX_SEARCH_LENGTH, PAGE_SIZE, parsePromotionQuery, toSearchString } from "./query";

describe("parsePromotionQuery", () => {
  it("applies defaults for an empty URL", () => {
    expect(parsePromotionQuery({})).toEqual({
      q: undefined,
      bank: undefined,
      category: undefined,
      status: "active",
      sort: "newest",
      page: 1,
      pageSize: PAGE_SIZE,
    });
  });

  it("reads valid values", () => {
    const query = parsePromotionQuery({
      q: "  pizza ",
      bank: "sampath",
      category: "dining",
      status: "upcoming",
      sort: "discount",
      page: "3",
    });
    expect(query).toMatchObject({
      q: "pizza",
      bank: "sampath",
      category: "dining",
      status: "upcoming",
      sort: "discount",
      page: 3,
    });
  });

  it("treats status=all as no status filter", () => {
    expect(parsePromotionQuery({ status: "all" }).status).toBeUndefined();
  });

  it("ignores unknown or malformed values", () => {
    const query = parsePromotionQuery({
      bank: "hsbc",
      category: "toys",
      status: "soon",
      sort: "random",
      page: "-2",
      q: "   ",
    });
    expect(query).toMatchObject({
      q: undefined,
      bank: undefined,
      category: undefined,
      status: "active",
      sort: "newest",
      page: 1,
    });
  });

  it("trims searches to the length the API accepts", () => {
    expect(parsePromotionQuery({ q: "a".repeat(150) }).q).toHaveLength(MAX_SEARCH_LENGTH);
  });

  it("uses the first value of repeated params", () => {
    expect(parsePromotionQuery({ bank: ["sampath", "combank"] }).bank).toBe("sampath");
  });
});

describe("toSearchString", () => {
  it("omits defaults", () => {
    expect(toSearchString(parsePromotionQuery({}))).toBe("");
  });

  it("round-trips through parsePromotionQuery", () => {
    const params = { q: "keells", bank: "combank", category: "supermarket", status: "all", sort: "ending_soon", page: "2" };
    const search = toSearchString(parsePromotionQuery(params));
    expect(Object.fromEntries(new URLSearchParams(search))).toEqual(params);
  });
});
