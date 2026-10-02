import { redirect } from "next/navigation";
import { FilterBar } from "@/components/filter-bar";
import { EmptyState } from "@/components/empty-state";
import { Hero } from "@/components/hero";
import { Pagination } from "@/components/pagination";
import { PromotionCard } from "@/components/promotion-card";
import { SampleDataNotice } from "@/components/sample-data-notice";
import { isEndingSoon } from "@/lib/format";
import { BANKS, getRepository, isUsingMockData } from "@/lib/promotions";
import { parsePromotionQuery, toSearchString } from "@/lib/promotions/query";
import { comparePromotions } from "@/lib/promotions/sort";

/** Enough of the soonest-ending offers to count those ending this week. */
const ENDING_SCAN_SIZE = 50;

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const query = parsePromotionQuery(await searchParams);
  const repository = getRepository();
  const now = new Date();

  const [results, categories, endingSoonest, ...topByBank] = await Promise.all([
    repository.listPromotions(query),
    repository.listCategories(query.status),
    repository.listPromotions({ status: "active", sort: "ending_soon", page: 1, pageSize: ENDING_SCAN_SIZE }),
    ...BANKS.map((bank) =>
      repository.listPromotions({ bank: bank.code, status: "active", sort: "discount", page: 1, pageSize: 2 }),
    ),
  ]);
  // Best offer from each bank, biggest first, then the runners-up, so the
  // hero always shows both banks.
  const [best, runnersUp] = [0, 1].map((rank) =>
    topByBank.map((page) => page.items[rank]).filter((p) => p !== undefined),
  );
  const featured = [...best.sort(comparePromotions.discount), ...runnersUp];

  // A stale link can point past the last page; send it to the last real one.
  const pageCount = Math.ceil(results.total / query.pageSize);
  if (pageCount > 0 && query.page > pageCount) {
    redirect(`/${toSearchString({ ...query, page: pageCount })}#offers`);
  }

  const firstShown = (query.page - 1) * query.pageSize + 1;
  const lastShown = firstShown + results.items.length - 1;

  return (
    <>
      <Hero
        featured={featured}
        activeCount={endingSoonest.total}
        endingThisWeek={endingSoonest.items.filter((p) => isEndingSoon(p, now)).length}
      />

      <section id="offers" aria-labelledby="offers-heading" className="mx-auto w-full max-w-7xl scroll-mt-4 px-4 sm:px-6">
        <h2 id="offers-heading" className="sr-only">Offers</h2>
        <FilterBar query={query} categories={categories} />

        {isUsingMockData() && <SampleDataNotice />}

        <p className="mb-6 mt-8 text-sm text-muted" aria-live="polite">
          {results.total === 0
            ? "No offers found"
            : `Showing ${firstShown}–${lastShown} of ${results.total} offers`}
        </p>

        {results.items.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {results.items.map((promotion) => (
              <li key={promotion.id}>
                <PromotionCard promotion={promotion} now={now} />
              </li>
            ))}
          </ul>
        )}

        <Pagination query={query} total={results.total} />
      </section>
    </>
  );
}
