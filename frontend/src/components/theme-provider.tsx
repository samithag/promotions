"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";

/** Dark by default; the visitor's choice is remembered by next-themes. */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
      {children}
    </NextThemesProvider>
  );
}
