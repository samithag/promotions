/** Primary pill button style, shared by links and buttons. */
export const buttonClass =
  "inline-flex items-center gap-2 rounded-full bg-text px-5 py-2.5 text-sm font-semibold text-bg";

interface MessageProps {
  title: string;
  children: React.ReactNode;
  action: React.ReactNode;
  as?: "h1" | "h3";
  className?: string;
}

/** A centered title, explanation and next step: for empty, error and 404 states. */
export function Message({ title, children, action, as: Heading = "h1", className = "" }: MessageProps) {
  return (
    <div className={`mx-auto px-6 text-center ${className}`}>
      <Heading className="display text-3xl font-bold">{title}</Heading>
      <p className="mx-auto mt-3 max-w-[44ch] text-muted">{children}</p>
      <div className="mt-8">{action}</div>
    </div>
  );
}
