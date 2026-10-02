import {
  BANKS,
  CATEGORIES,
  SORTS,
  STATUSES,
  type BankCode,
  type CategorySlug,
  type PromotionQuery,
  type PromotionStatus,
  type SortOrder,
} from "./types";

export const PAGE_SIZE = 12;
/** The API rejects longer searches. */
export const MAX_SEARCH_LENGTH = 100;

/** Status shown when the URL doesn't name one. */
export const DEFAULT_STATUS: PromotionStatus = "active";
/** URL value for "no status filter". */
export const ALL_STATUSES = "all";
export const DEFAULT_SORT: SortOrder = "newest";

type RawSearchParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function oneOf<T extends string>(
  value: string | undefined,
  allowed: readonly T[],
): T | undefined {
  return allowed.find((item) => item === value);
}

/**
 * Turns URL search params into a validated query. Unknown or malformed values
 * fall back to defaults rather than erroring, so hand-edited URLs still work.
 */
export function parsePromotionQuery(params: RawSearchParams): PromotionQuery {
  const q = first(params.q)?.trim().slice(0, MAX_SEARCH_LENGTH).trim();
  const rawStatus = first(params.status);
  const page = Number.parseInt(first(params.page) ?? "", 10);

  return {
    q: q || undefined,
    bank: oneOf<BankCode>(first(params.bank), BANKS.map((b) => b.code)),
    category: oneOf<CategorySlug>(
      first(params.category),
      CATEGORIES.map((c) => c.slug),
    ),
    status:
      rawStatus === ALL_STATUSES
        ? undefined
        : (oneOf(rawStatus, STATUSES) ?? DEFAULT_STATUS),
    sort: oneOf(first(params.sort), SORTS.map((s) => s.value)) ?? DEFAULT_SORT,
    page: Number.isFinite(page) && page > 0 ? page : 1,
    pageSize: PAGE_SIZE,
  };
}

/**
 * Builds the `?query` string for a query, leaving out defaults so URLs stay
 * short. The inverse of `parsePromotionQuery`.
 */
export function toSearchString(query: Omit<PromotionQuery, "pageSize">): string {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.bank) params.set("bank", query.bank);
  if (query.category) params.set("category", query.category);
  if (query.status !== DEFAULT_STATUS) params.set("status", query.status ?? ALL_STATUSES);
  if (query.sort !== DEFAULT_SORT) params.set("sort", query.sort);
  if (query.page > 1) params.set("page", String(query.page));
  const search = params.toString();
  return search ? `?${search}` : "";
}
