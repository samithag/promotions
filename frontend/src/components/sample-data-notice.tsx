import { Info } from "lucide-react";

/** Shown while the site runs on built-in sample data instead of the scraper API. */
export function SampleDataNotice() {
  return (
    <p className="mt-6 flex items-start gap-2.5 rounded-2xl bg-surface-2 px-4 py-3 text-sm text-muted">
      <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
      These are sample offers for previewing the site. Live offers appear once
      the site is connected to the scraper.
    </p>
  );
}
