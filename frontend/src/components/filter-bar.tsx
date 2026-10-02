"use client";

import { Search, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";
import { ALL_STATUSES, toSearchString } from "@/lib/promotions/query";
import {
  BANKS,
  SORTS,
  STATUS_FILTERS,
  type CategoryCount,
  type PromotionQuery,
} from "@/lib/promotions/types";

const SEARCH_DEBOUNCE_MS = 300;

interface FilterBarProps {
  query: PromotionQuery;
  categories: CategoryCount[];
}

/**
 * Search, filter and sort controls. All state lives in the URL: each change
 * navigates, and the server re-renders the results.
 */
export function FilterBar({ query, categories }: FilterBarProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  // Local text so typing stays responsive. When the URL's q changes, the box
  // is overwritten only if the new value isn't the one this bar pushed itself
  // (e.g. "Clear filters" or the back button), so typing is never clobbered.
  const [text, setText] = useState(query.q ?? "");
  const [seenQ, setSeenQ] = useState(query.q);
  const [pushedQ, setPushedQ] = useState(query.q);
  if (query.q !== seenQ) {
    setSeenQ(query.q);
    if (query.q !== pushedQ) {
      setPushedQ(query.q);
      setText(query.q ?? "");
    }
  }

  const debounce = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(debounce.current), []);

  /** Navigates to the current filters plus `patch`, including any typed text. */
  function update(patch: Partial<PromotionQuery>, searchText = text) {
    // A pending search would navigate with stale filters, so fold it in now.
    clearTimeout(debounce.current);
    const q = searchText.trim() || undefined;
    setPushedQ(q);
    // Any filter change starts again from page 1.
    const next = { ...query, q, page: 1, ...patch };
    startTransition(() => {
      router.replace(`/${toSearchString(next)}`, { scroll: false });
    });
  }

  function onSearchChange(value: string) {
    setText(value);
    clearTimeout(debounce.current);
    debounce.current = setTimeout(() => update({}, value), SEARCH_DEBOUNCE_MS);
  }

  return (
    <div className="sticky top-0 z-20 -mx-4 border-b border-line bg-bg/85 px-4 py-4 backdrop-blur-md sm:-mx-6 sm:px-6">
      {/* Thin progress line while the server re-renders results. */}
      <div
        className={`absolute inset-x-0 bottom-0 h-0.5 origin-left bg-gold transition-transform duration-500 ${isPending ? "scale-x-100" : "scale-x-0"}`}
        aria-hidden
      />

      <div className="flex flex-wrap items-center gap-3">
        <label className="relative min-w-0 flex-1 basis-64">
          <span className="sr-only">Search offers</span>
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" aria-hidden />
          <input
            type="search"
            value={text}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search merchants or offers"
            className="h-11 w-full rounded-full border border-line bg-surface pl-10 pr-10 text-[15px] placeholder:text-muted focus:border-focus focus:outline-none [&::-webkit-search-cancel-button]:hidden"
          />
          {text && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="absolute right-2 top-1/2 grid size-7 -translate-y-1/2 place-items-center rounded-full text-muted hover:text-text"
              aria-label="Clear search"
            >
              <X className="size-4" aria-hidden />
            </button>
          )}
        </label>

        <div role="group" aria-label="Bank" className="flex h-11 rounded-full border border-line bg-surface p-1">
          {[{ code: undefined, shortName: "All banks" }, ...BANKS].map((bank) => (
            <button
              key={bank.shortName}
              type="button"
              aria-pressed={query.bank === bank.code}
              onClick={() => update({ bank: bank.code })}
              className="rounded-full px-4 text-sm font-medium text-muted transition-colors hover:text-text aria-pressed:bg-text aria-pressed:text-bg"
            >
              {bank.shortName}
            </button>
          ))}
        </div>

        <Select
          label="Status"
          value={query.status ?? ALL_STATUSES}
          options={STATUS_FILTERS}
          onChange={(value) => update({ status: value === ALL_STATUSES ? undefined : (value as PromotionQuery["status"]) })}
        />
        <Select
          label="Sort by"
          value={query.sort}
          options={SORTS}
          onChange={(value) => update({ sort: value as PromotionQuery["sort"] })}
        />
      </div>

      <div role="group" aria-label="Category" className="rail -mx-4 mt-3 flex gap-2 overflow-x-auto px-4 sm:-mx-6 sm:px-6">
        <CategoryChip pressed={!query.category} onClick={() => update({ category: undefined })}>
          All categories
        </CategoryChip>
        {categories.map((category) => (
          <CategoryChip
            key={category.slug}
            pressed={query.category === category.slug}
            onClick={() => update({ category: category.slug })}
          >
            {category.label}
            <span className="tabular-nums opacity-60">{category.count}</span>
          </CategoryChip>
        ))}
      </div>
    </div>
  );
}

function CategoryChip({ pressed, onClick, children }: { pressed: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className="flex shrink-0 items-center gap-1.5 rounded-full border border-line px-3.5 py-1.5 text-sm font-medium text-muted transition-colors hover:text-text aria-pressed:border-gold aria-pressed:text-text"
    >
      {children}
    </button>
  );
}

interface SelectProps {
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}

function Select({ label, value, options, onChange }: SelectProps) {
  return (
    <label className="flex h-11 items-center gap-2 rounded-full border border-line bg-surface pl-4 pr-2 text-sm has-focus-visible:outline-2 has-focus-visible:outline-offset-3 has-focus-visible:outline-focus">
      <span className="text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-full cursor-pointer bg-transparent pr-1 font-medium focus:outline-none"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value} className="bg-surface text-text">
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
