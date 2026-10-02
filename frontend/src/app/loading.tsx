/** Skeleton shown while the first page of offers loads. */
export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 pt-8 sm:px-6" aria-busy="true" aria-label="Loading offers">
      <div className="h-40 max-w-2xl animate-pulse rounded-3xl bg-surface motion-reduce:animate-none" />
      <ul className="mt-16 grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }, (_, i) => (
          <li key={i} className="aspect-[1.586] animate-pulse rounded-2xl bg-surface motion-reduce:animate-none" />
        ))}
      </ul>
    </div>
  );
}
