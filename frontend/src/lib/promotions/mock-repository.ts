import { buildMockPromotions } from "./mock-data";
import { comparePromotions } from "./sort";
import { getStatus } from "./status";
import {
  CATEGORIES,
  type CategoryCount,
  type Page,
  type Promotion,
  type PromotionQuery,
  type PromotionStatus,
  type PromotionsRepository,
} from "./types";

function hasStatus(promotion: Promotion, status: PromotionStatus | undefined, now: Date): boolean {
  return !status || getStatus(promotion, now) === status;
}

function matchesText(promotion: Promotion, q: string): boolean {
  const needle = q.toLowerCase();
  return [promotion.title, promotion.merchant, promotion.description].some(
    (field) => field.toLowerCase().includes(needle),
  );
}

/**
 * Filters, sorts and paginates promotions in memory, the same way the planned
 * `GET /api/v1/promotions` endpoint does on the server.
 */
export function queryPromotions(
  promotions: Promotion[],
  query: PromotionQuery,
  now: Date,
): Page<Promotion> {
  const matches = promotions
    .filter((p) => !query.bank || p.bank === query.bank)
    .filter((p) => !query.category || p.category === query.category)
    .filter((p) => hasStatus(p, query.status, now))
    .filter((p) => !query.q || matchesText(p, query.q))
    .sort(comparePromotions[query.sort]);

  const start = (query.page - 1) * query.pageSize;
  return {
    items: matches.slice(start, start + query.pageSize),
    total: matches.length,
    page: query.page,
    page_size: query.pageSize,
  };
}

export function countCategories(
  promotions: Promotion[],
  status: PromotionStatus | undefined,
  now: Date,
): CategoryCount[] {
  const inScope = promotions.filter((p) => hasStatus(p, status, now));
  return CATEGORIES.map(({ slug, label }) => ({
    slug,
    label,
    count: inScope.filter((p) => p.category === slug).length,
  }));
}

/** Serves sample data while the FastAPI backend (SCRUM-1) is being built. */
export const mockRepository: PromotionsRepository = {
  async listPromotions(query) {
    const now = new Date();
    return queryPromotions(buildMockPromotions(now), query, now);
  },
  async getPromotion(id) {
    return buildMockPromotions(new Date()).find((p) => p.id === id) ?? null;
  },
  async listCategories(status) {
    const now = new Date();
    return countCategories(buildMockPromotions(now), status, now);
  },
};
