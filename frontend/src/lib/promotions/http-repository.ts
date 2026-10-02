import type {
  CategoryCount,
  Page,
  Promotion,
  PromotionsRepository,
} from "./types";

/** Promotions are scraped hourly, so a few minutes of caching is plenty fresh. */
const REVALIDATE_SECONDS = 300;

type Params = Record<string, string | number | undefined>;

/** Builds an API URL, keeping any path prefix on the base URL. */
export function apiUrl(baseUrl: string, path: string, params: Params = {}): URL {
  const url = new URL(`${baseUrl.replace(/\/+$/, "")}/api/v1${path}`);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  return url;
}

/**
 * Reads promotions from the FastAPI backend (`/api/v1`, see
 * `doc/webscraper_plan.md`). Query params are passed through using the API's
 * names. Failures throw, so the page shows its error state rather than an
 * empty list.
 */
export function createHttpRepository(baseUrl: string): PromotionsRepository {
  async function request(path: string, params?: Params): Promise<Response> {
    const url = apiUrl(baseUrl, path, params);
    const response = await fetch(url, { next: { revalidate: REVALIDATE_SECONDS } });
    if (!response.ok && response.status !== 404) {
      throw new Error(`GET ${url.pathname} failed with ${response.status}`);
    }
    return response;
  }

  /** GETs JSON; a 404 is an error here, since these endpoints always exist. */
  async function get<T>(path: string, params?: Params): Promise<T> {
    const response = await request(path, params);
    if (response.status === 404) {
      throw new Error(`GET ${response.url || path} returned 404; check PROMOTIONS_API_URL`);
    }
    return (await response.json()) as T;
  }

  return {
    listPromotions(query) {
      return get<Page<Promotion>>("/promotions", {
        q: query.q,
        bank: query.bank,
        category: query.category,
        status: query.status,
        sort: query.sort,
        page: query.page,
        page_size: query.pageSize,
      });
    },
    async getPromotion(id) {
      // Here a 404 means the offer doesn't exist.
      const response = await request(`/promotions/${encodeURIComponent(id)}`);
      return response.status === 404 ? null : ((await response.json()) as Promotion);
    },
    listCategories(status) {
      return get<CategoryCount[]>("/categories", { status });
    },
  };
}
