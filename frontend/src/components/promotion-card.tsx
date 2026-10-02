import Link from "next/link";
import { formatValidity, getBank, isEndingSoon } from "@/lib/format";
import { getStatus, type Promotion } from "@/lib/promotions";
import { CardFace } from "./card-face";

export function PromotionCard({ promotion, now }: { promotion: Promotion; now: Date }) {
  const status = getStatus(promotion, now);
  const endingSoon = isEndingSoon(promotion, now);

  return (
    <Link href={`/promotions/${promotion.id}`} className="group block rounded-2xl">
      <CardFace
        promotion={promotion}
        expired={status === "expired"}
        className="transition-transform duration-300 group-hover:-translate-y-1"
      />
      <div className="mt-3 px-1">
        <h3 className="font-semibold leading-snug group-hover:underline">
          <span className="sr-only">{promotion.merchant}, {getBank(promotion.bank).name}: </span>
          {promotion.title}
        </h3>
        <p className={`mt-1 text-sm ${endingSoon ? "font-medium text-gold" : "text-muted"}`}>
          {formatValidity(promotion, now)}
        </p>
      </div>
    </Link>
  );
}
