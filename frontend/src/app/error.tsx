"use client";

import { buttonClass, Message } from "@/components/message";

/** Shown when the offers service fails to respond. */
export default function Error({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <Message
      title="Offers couldn't be loaded"
      action={<button type="button" onClick={() => retry()} className={buttonClass}>Try again</button>}
      className="max-w-xl py-24"
    >
      The offers service didn&apos;t respond. Check your connection and try again.
    </Message>
  );
}
