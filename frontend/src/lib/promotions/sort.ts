import type { Promotion, SortOrder } from "./types";

/**
 * Ranks discounts for the "Biggest discount" sort: percentages first (by
 * size), then fixed rupee amounts, then installment plans, then unknown.
 */
function discountRank(promotion: Promotion): [number, number] {
  const value = promotion.discount_value ?? 0;
  switch (promotion.discount_type) {
    case "percentage":
      return [0, -value];
    case "fixed":
      return [1, -value];
    case "installment":
      return [2, -value];
    default:
      return [3, 0];
  }
}

/** Comparators for each sort order, matching the API's ordering. */
export const comparePromotions: Record<SortOrder, (a: Promotion, b: Promotion) => number> = {
  newest: (a, b) => b.first_seen_at.localeCompare(a.first_seen_at),
  // Open-ended offers have no deadline, so they sort last.
  ending_soon: (a, b) =>
    (a.valid_to ?? "9999-12-31").localeCompare(b.valid_to ?? "9999-12-31"),
  discount: (a, b) => {
    const [groupA, valueA] = discountRank(a);
    const [groupB, valueB] = discountRank(b);
    return groupA - groupB || valueA - valueB;
  },
};
