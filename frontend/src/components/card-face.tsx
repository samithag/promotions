import { categoryLabel, formatDiscount, getBank } from "@/lib/format";
import type { Promotion } from "@/lib/promotions";
import { CategoryIcon } from "./category-icon";

interface CardFaceProps {
  promotion: Promotion;
  expired?: boolean;
  size?: "md" | "lg";
  className?: string;
}

/**
 * A promotion drawn as the bank's payment card: bank name, EMV chip, the
 * discount embossed in foil, and the merchant where the cardholder name sits.
 * Decorative only; the surrounding markup carries the accessible text.
 */
export function CardFace({ promotion, expired = false, size = "md", className = "" }: CardFaceProps) {
  const bank = getBank(promotion.bank);
  const { figure, caption } = formatDiscount(promotion);
  const large = size === "lg";

  return (
    <div
      aria-hidden
      className={`card-face face-${promotion.bank} ${expired ? "face-expired" : ""} flex flex-col justify-between rounded-[4.5%/7%] ${large ? "p-7 sm:p-9" : "p-5"} ${className}`}
    >
      <div className="flex items-start justify-between">
        <span className={`display font-bold ${large ? "text-2xl" : "text-base"}`}>{bank.shortName}</span>
        <span className={`flex items-center gap-1.5 rounded-full bg-white/15 font-medium backdrop-blur-sm ${large ? "px-3 py-1.5 text-sm" : "px-2 py-1 text-xs"}`}>
          <CategoryIcon category={promotion.category} className={large ? "size-4" : "size-3.5"} />
          {categoryLabel(promotion.category)}
        </span>
      </div>

      <div className="flex items-end gap-3">
        <Chip className={large ? "w-12" : "w-8"} />
        <p className="flex items-baseline gap-2">
          <span className={`foil ${large ? "text-7xl sm:text-8xl" : figure.length > 5 ? "text-4xl" : "text-5xl"}`}>{figure}</span>
          <span className={`font-medium text-white/85 ${large ? "text-lg" : "text-sm"}`}>{caption}</span>
        </p>
      </div>

      <p className={`truncate font-semibold tracking-wide text-white/90 ${large ? "text-xl" : "text-sm"}`}>
        {promotion.merchant}
      </p>
    </div>
  );
}

/** A simplified EMV chip. */
function Chip({ className }: { className: string }) {
  return (
    <svg viewBox="0 0 40 30" className={`${className} mb-1 shrink-0`}>
      <rect width="40" height="30" rx="5" fill="#e9cf8a" />
      <path d="M0 10h13M0 20h13M27 10h13M27 20h13M13 0v30M27 0v30M13 15h14" stroke="#b8913f" strokeWidth="1.2" fill="none" />
    </svg>
  );
}
