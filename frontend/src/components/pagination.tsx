import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import type { PromotionQuery } from "@/lib/promotions";
import { toSearchString } from "@/lib/promotions/query";

interface PaginationProps {
  query: PromotionQuery;
  total: number;
}

export function Pagination({ query, total }: PaginationProps) {
  const pageCount = Math.ceil(total / query.pageSize);
  if (pageCount <= 1) return null;

  const href = (page: number) => `/${toSearchString({ ...query, page })}#offers`;

  return (
    <nav aria-label="Pages" className="mt-14 flex items-center justify-center gap-4">
      <PageLink href={query.page > 1 ? href(query.page - 1) : undefined}>
        <ChevronLeft className="size-4" aria-hidden /> Previous
      </PageLink>
      <span className="text-sm text-muted">
        Page {query.page} of {pageCount}
      </span>
      <PageLink href={query.page < pageCount ? href(query.page + 1) : undefined}>
        Next <ChevronRight className="size-4" aria-hidden />
      </PageLink>
    </nav>
  );
}

/** A link, or a dimmed placeholder when there's no page to go to. */
function PageLink({ href, children }: { href?: string; children: React.ReactNode }) {
  const className =
    "flex items-center gap-1 rounded-full border border-line px-4 py-2 text-sm font-medium transition-colors hover:bg-surface-2";
  return href ? (
    <Link href={href} className={className}>{children}</Link>
  ) : (
    <span className={`${className} pointer-events-none opacity-40`} aria-hidden>{children}</span>
  );
}
