import type { Promotion } from "./types";

/** Noon on 2 Oct 2026 in Sri Lanka (UTC+5:30). */
export const NOW = new Date("2026-10-02T06:30:00Z");

export function makePromotion(overrides: Partial<Promotion> = {}): Promotion {
  return {
    id: "1",
    bank: "combank",
    title: "20% off",
    merchant: "Merchant",
    description: "Description",
    discount_value: 20,
    discount_type: "percentage",
    card_types: ["Visa"],
    category: "dining",
    bank_category: "Food & Restaurants",
    valid_from: "2026-09-01",
    valid_to: "2026-10-31",
    image_url: null,
    source_url: "https://example.com",
    first_seen_at: "2026-09-01T00:00:00Z",
    last_seen_at: "2026-10-02T00:00:00Z",
    is_active: true,
    ...overrides,
  };
}
