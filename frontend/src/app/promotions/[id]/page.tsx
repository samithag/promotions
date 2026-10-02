import { ArrowLeft, ExternalLink } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";
import { CardFace } from "@/components/card-face";
import { buttonClass } from "@/components/message";
import { categoryLabel, formatDate, formatDateRange, formatValidity, getBank, isEndingSoon } from "@/lib/format";
import { getRepository, getStatus } from "@/lib/promotions";

// Shared by generateMetadata and the page so the offer is fetched once.
const getPromotion = cache((id: string) => getRepository().getPromotion(id));

export async function generateMetadata({ params }: PageProps<"/promotions/[id]">): Promise<Metadata> {
  const promotion = await getPromotion((await params).id);
  if (!promotion) return { title: "Offer not found" };
  return {
    title: `${promotion.merchant}: ${promotion.title}`,
    description: promotion.description,
  };
}

export default async function PromotionPage({ params }: PageProps<"/promotions/[id]">) {
  const promotion = await getPromotion((await params).id);
  if (!promotion) notFound();

  const now = new Date();
  const bank = getBank(promotion.bank);
  const status = getStatus(promotion, now);

  const facts = [
    { term: "Bank", detail: bank.name },
    {
      term: "Category",
      detail:
        promotion.bank_category && promotion.bank_category !== categoryLabel(promotion.category)
          ? `${categoryLabel(promotion.category)} (listed by the bank as ${promotion.bank_category})`
          : categoryLabel(promotion.category),
    },
    { term: "Valid", detail: formatDateRange(promotion) },
    { term: "Cards", detail: promotion.card_types.join(", ") || "Not specified" },
    { term: "Last checked", detail: formatDate(promotion.last_seen_at.slice(0, 10)) },
  ];

  return (
    <article className="mx-auto w-full max-w-7xl px-4 pt-4 sm:px-6">
      <Link href="/" className="inline-flex items-center gap-1.5 rounded-md text-sm font-medium text-muted hover:text-text">
        <ArrowLeft className="size-4" aria-hidden /> All offers
      </Link>

      <div className="mt-8 grid items-start gap-12 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
        <CardFace promotion={promotion} expired={status === "expired"} size="lg" className="lg:sticky lg:top-8" />

        <div>
          <p className="text-muted">{promotion.merchant}</p>
          <h1 className="display mt-2 text-4xl font-bold leading-[1.02] sm:text-5xl">{promotion.title}</h1>
          <p className={`mt-4 font-medium ${isEndingSoon(promotion, now) ? "text-gold" : status === "expired" ? "text-muted" : ""}`}>
            {formatValidity(promotion, now)}
          </p>

          <p className="mt-8 max-w-[62ch] text-lg leading-relaxed">{promotion.description}</p>

          <dl className="mt-10 divide-y divide-line border-y border-line">
            {facts.map(({ term, detail }) => (
              <div key={term} className="grid grid-cols-[8rem_1fr] gap-4 py-3.5">
                <dt className="text-muted">{term}</dt>
                <dd>{detail}</dd>
              </div>
            ))}
          </dl>

          <a
            href={promotion.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`${buttonClass} mt-10`}
          >
            See full terms on the {bank.shortName} website
            <ExternalLink className="size-4" aria-hidden />
            <span className="sr-only">(opens in a new tab)</span>
          </a>
        </div>
      </div>
    </article>
  );
}
