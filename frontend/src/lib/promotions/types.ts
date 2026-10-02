/**
 * Promotion domain types. These mirror the planned FastAPI `/api/v1` contract
 * described in `doc/webscraper_plan.md`, so the mock and HTTP repositories are
 * interchangeable.
 */

export const BANKS = [
  { code: "combank", name: "Commercial Bank", shortName: "ComBank" },
  { code: "sampath", name: "Sampath Bank", shortName: "Sampath" },
] as const;

export type BankCode = (typeof BANKS)[number]["code"];

export interface Bank {
  code: BankCode;
  name: string;
  shortName: string;
}

/** The shared category list both banks' offers are classified into. */
export const CATEGORIES = [
  { slug: "dining", label: "Dining" },
  { slug: "supermarket", label: "Supermarket" },
  { slug: "travel", label: "Travel" },
  { slug: "hotels", label: "Hotels" },
  { slug: "fashion", label: "Fashion" },
  { slug: "electronics", label: "Electronics" },
  { slug: "health", label: "Health" },
  { slug: "fuel", label: "Fuel" },
  { slug: "online", label: "Online" },
  { slug: "other", label: "Other" },
] as const;

export type CategorySlug = (typeof CATEGORIES)[number]["slug"];

export type DiscountType = "percentage" | "fixed" | "installment";

export interface Promotion {
  id: string;
  bank: BankCode;
  title: string;
  merchant: string;
  description: string;
  /** Percent for `percentage`, rupees for `fixed`, months for `installment`. */
  discount_value: number | null;
  discount_type: DiscountType | null;
  card_types: string[];
  category: CategorySlug;
  /** The category label as the bank itself shows it. */
  bank_category: string | null;
  /** ISO dates (YYYY-MM-DD). */
  valid_from: string | null;
  valid_to: string | null;
  image_url: string | null;
  source_url: string;
  /** ISO timestamps. */
  first_seen_at: string;
  last_seen_at: string;
  is_active: boolean;
}

export const STATUSES = ["active", "upcoming", "expired"] as const;
export type PromotionStatus = (typeof STATUSES)[number];

/** Status filter choices; "all" (no status filter) is a URL-only value. */
export const STATUS_FILTERS = [
  { value: "active", label: "Running now" },
  { value: "upcoming", label: "Starting soon" },
  { value: "expired", label: "Ended" },
  { value: "all", label: "All offers" },
] as const satisfies readonly { value: PromotionStatus | "all"; label: string }[];

export const SORTS = [
  { value: "newest", label: "Newest" },
  { value: "ending_soon", label: "Ending soon" },
  { value: "discount", label: "Biggest discount" },
] as const;
export type SortOrder = (typeof SORTS)[number]["value"];

export interface PromotionQuery {
  q?: string;
  bank?: BankCode;
  category?: CategorySlug;
  /** `undefined` means every status. */
  status?: PromotionStatus;
  sort: SortOrder;
  page: number;
  pageSize: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CategoryCount {
  slug: CategorySlug;
  label: string;
  count: number;
}

export interface PromotionsRepository {
  listPromotions(query: PromotionQuery): Promise<Page<Promotion>>;
  getPromotion(id: string): Promise<Promotion | null>;
  /** Offer counts per category, for the given status (all when undefined). */
  listCategories(status?: PromotionStatus): Promise<CategoryCount[]>;
}
