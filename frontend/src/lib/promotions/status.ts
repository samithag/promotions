import type { Promotion, PromotionStatus } from "./types";

/** Validity dates are Sri Lankan calendar dates, so "today" is judged there. */
const TIME_ZONE = "Asia/Colombo";

/** Today's date as `YYYY-MM-DD` in Sri Lanka. ISO dates compare as strings. */
export function isoDate(now: Date): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE }).format(now);
}

/**
 * Derives a promotion's status. Offers the scraper no longer sees
 * (`is_active: false`) count as expired even if their end date hasn't passed.
 */
export function getStatus(promotion: Promotion, now: Date): PromotionStatus {
  const today = isoDate(now);
  if (!promotion.is_active) return "expired";
  if (promotion.valid_to && promotion.valid_to < today) return "expired";
  if (promotion.valid_from && promotion.valid_from > today) return "upcoming";
  return "active";
}

/** Whole days until the offer's last day (0 means it ends today). `null` if open-ended. */
export function daysLeft(promotion: Promotion, now: Date): number | null {
  if (!promotion.valid_to) return null;
  const end = Date.parse(promotion.valid_to);
  const today = Date.parse(isoDate(now));
  return Math.round((end - today) / 86_400_000);
}
