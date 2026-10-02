import Link from "next/link";
import type { Promotion } from "@/lib/promotions";
import { CardFace } from "./card-face";

interface HeroProps {
  /** Up to three offers to fan out; the first ends up on top. */
  featured: Promotion[];
  activeCount: number;
  endingThisWeek: number;
}

// Back card first, so the biggest offer ends up on top.
const FAN = [
  { rotate: -14, x: "-18%", y: "6%", delay: 120 },
  { rotate: 9, x: "16%", y: "2%", delay: 60 },
  { rotate: -3, x: "0%", y: "-6%", delay: 0 },
];

export function Hero({ featured, activeCount, endingThisWeek }: HeroProps) {
  const fanned = featured.slice(0, 3).reverse();
  const fan = FAN.slice(FAN.length - fanned.length);

  return (
    <section className="mx-auto grid w-full max-w-7xl items-center gap-12 px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:pb-24 lg:pt-14">
      <div>
        <h1 className="display max-w-[16ch] text-5xl font-bold leading-[0.95] sm:text-6xl lg:text-7xl">
          Every card offer from ComBank and Sampath, in one place.
        </h1>
        <p className="mt-6 max-w-[52ch] text-lg leading-relaxed text-muted">
          We check both banks&apos; promotion pages every hour and sort what we
          find by category, so you can see what your card gets you today.
        </p>
        <p className="mt-8 text-lg">
          <span className="font-semibold">{activeCount} offers</span> running now.{" "}
          {endingThisWeek > 0 && (
            <Link href="/?sort=ending_soon#offers" className="font-semibold text-gold underline-offset-4 hover:underline">
              {endingThisWeek} end this week.
            </Link>
          )}
        </p>
      </div>

      {fanned.length > 0 && (
        <div className="relative mx-auto aspect-[1.35] w-full max-w-sm sm:max-w-md lg:max-w-lg" aria-hidden>
          {fanned.map((promotion, i) => (
            <div
              key={promotion.id}
              className="fan-card absolute inset-x-[12%] top-[18%]"
              style={{
                transform: `translate(${fan[i].x}, ${fan[i].y}) rotate(${fan[i].rotate}deg)`,
                animationDelay: `${fan[i].delay}ms`,
              }}
            >
              <CardFace promotion={promotion} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
