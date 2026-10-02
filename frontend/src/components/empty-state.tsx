import Link from "next/link";
import { buttonClass, Message } from "./message";

export function EmptyState() {
  return (
    <Message
      as="h3"
      title="No offers match these filters"
      action={<Link href="/#offers" className={buttonClass}>Clear filters</Link>}
      className="rounded-3xl border border-dashed border-line py-20"
    >
      Try another search term, or widen the bank, category or status.
    </Message>
  );
}
