import Link from "next/link";
import { buttonClass, Message } from "@/components/message";

export default function NotFound() {
  return (
    <Message
      title="This offer isn't here"
      action={<Link href="/" className={buttonClass}>Browse all offers</Link>}
      className="max-w-xl py-24"
    >
      It may have been removed by the bank, or the link is wrong.
    </Message>
  );
}
