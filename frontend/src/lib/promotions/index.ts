import { createHttpRepository } from "./http-repository";
import { mockRepository } from "./mock-repository";
import type { PromotionsRepository } from "./types";

// Server-side entry point. Client components import from "./types" and
// "./query" directly so they don't pull in the repositories or process.env.
export { getStatus } from "./status";
export * from "./types";

/** True when no backend is configured and the site shows sample data. */
export function isUsingMockData(): boolean {
  return !process.env.PROMOTIONS_API_URL;
}

/**
 * Picks the data source: the FastAPI backend when `PROMOTIONS_API_URL` is set,
 * otherwise built-in sample data. Server-side only.
 */
export function getRepository(): PromotionsRepository {
  const baseUrl = process.env.PROMOTIONS_API_URL;
  return baseUrl ? createHttpRepository(baseUrl) : mockRepository;
}
