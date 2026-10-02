import { afterEach, describe, expect, it, vi } from "vitest";
import { apiUrl, createHttpRepository } from "./http-repository";
import { parsePromotionQuery } from "./query";
import { makePromotion } from "./test-utils";

function mockFetch(status: number, body: unknown = null) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const requestedUrl = (fetchMock: ReturnType<typeof mockFetch>) =>
  String((fetchMock.mock.calls[0] as unknown[])[0]);

afterEach(() => vi.unstubAllGlobals());

describe("apiUrl", () => {
  it("keeps a path prefix on the base URL and drops trailing slashes", () => {
    expect(apiUrl("https://host/prefix/", "/banks").href).toBe("https://host/prefix/api/v1/banks");
  });

  it("omits undefined params", () => {
    expect(apiUrl("https://host", "/promotions", { q: undefined, page: 2 }).search).toBe("?page=2");
  });
});

describe("createHttpRepository", () => {
  const repository = createHttpRepository("https://api.test");

  it("passes the query to /promotions using the API's param names", async () => {
    const page = { items: [], total: 0, page: 1, page_size: 12 };
    const fetchMock = mockFetch(200, page);
    const query = parsePromotionQuery({ bank: "sampath", status: "all", sort: "discount" });

    await expect(repository.listPromotions(query)).resolves.toEqual(page);
    expect(requestedUrl(fetchMock)).toBe(
      "https://api.test/api/v1/promotions?bank=sampath&sort=discount&page=1&page_size=12",
    );
  });

  it("returns a promotion, or null when it doesn't exist", async () => {
    const promotion = makePromotion({ id: "a b" });
    const fetchMock = mockFetch(200, promotion);
    await expect(repository.getPromotion("a b")).resolves.toEqual(promotion);
    expect(requestedUrl(fetchMock)).toBe("https://api.test/api/v1/promotions/a%20b");

    mockFetch(404);
    await expect(repository.getPromotion("missing")).resolves.toBeNull();
  });

  it("throws on a 404 from a list endpoint, which means a bad base URL", async () => {
    mockFetch(404);
    await expect(repository.listCategories()).rejects.toThrow(/404/);
  });

  it("throws on server errors", async () => {
    mockFetch(500);
    await expect(repository.listPromotions(parsePromotionQuery({}))).rejects.toThrow(/500/);
  });
});
