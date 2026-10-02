import { daysLeft, getStatus } from "@/lib/promotions/status";
import { BANKS, CATEGORIES, type Bank, type BankCode, type CategorySlug, type Promotion } from "@/lib/promotions/types";

const rupees = new Intl.NumberFormat("en-LK", { maximumFractionDigits: 0 });

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

export function getBank(code: BankCode): Bank {
  return BANKS.find((bank) => bank.code === code) ?? BANKS[0];
}

export function categoryLabel(slug: CategorySlug): string {
  return CATEGORIES.find((c) => c.slug === slug)?.label ?? "Other";
}

/** Splits a discount into the big figure and the words after it. */
export function formatDiscount(promotion: Promotion): { figure: string; caption: string } {
  const value = promotion.discount_value;
  if (value === null) return { figure: "Deal", caption: "see details" };
  switch (promotion.discount_type) {
    case "percentage":
      return { figure: `${value}%`, caption: "off" };
    case "fixed":
      return { figure: `Rs ${rupees.format(value)}`, caption: "off" };
    case "installment":
      return { figure: "0%", caption: `for ${value} months` };
    default:
      return { figure: "Deal", caption: "see details" };
  }
}

/** Formats an ISO date (YYYY-MM-DD) as "12 Oct 2026". */
export function formatDate(iso: string): string {
  return dateFormat.format(new Date(`${iso}T00:00:00Z`));
}

/** The full validity window, e.g. "1 Oct 2026 to 31 Oct 2026". */
export function formatDateRange({ valid_from: from, valid_to: to }: Promotion): string {
  if (from && to) return `${formatDate(from)} to ${formatDate(to)}`;
  if (to) return `Until ${formatDate(to)}`;
  if (from) return `From ${formatDate(from)}, no end date`;
  return "No dates given";
}

/** A short line saying when an offer runs, phrased for its current status. */
export function formatValidity(promotion: Promotion, now: Date): string {
  const status = getStatus(promotion, now);
  const { valid_from: from, valid_to: to } = promotion;

  if (status === "upcoming" && from) return `Starts ${formatDate(from)}`;
  if (status === "expired") return to ? `Ended ${formatDate(to)}` : "Ended";
  if (!to) return "No end date";

  const days = daysLeft(promotion, now);
  if (days === 0) return "Ends today";
  if (days === 1) return "Ends tomorrow";
  if (days !== null && days <= 7) return `Ends in ${days} days`;
  return `Until ${formatDate(to)}`;
}

/** True when an active offer ends within a week, worth flagging visually. */
export function isEndingSoon(promotion: Promotion, now: Date): boolean {
  const days = daysLeft(promotion, now);
  return getStatus(promotion, now) === "active" && days !== null && days <= 7;
}
