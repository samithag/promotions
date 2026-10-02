import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";

export function SiteHeader() {
  return (
    <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-5 sm:px-6">
      <Link href="/" className="flex items-center gap-2.5 rounded-md">
        {/* Two overlapping cards in the banks' colors. */}
        <span className="relative h-5 w-8" aria-hidden>
          <span className="absolute left-0 top-0 h-4 w-6 rounded-[3px] bg-[#1f5bd8]" />
          <span className="absolute bottom-0 right-0 h-4 w-6 rounded-[3px] bg-[#f47b20] ring-2 ring-bg" />
        </span>
        <span className="display text-xl font-bold">Promotions</span>
      </Link>
      <ThemeToggle />
    </header>
  );
}
