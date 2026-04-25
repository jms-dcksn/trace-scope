import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = { title: "Agent Eval" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 min-h-screen">
        <header className="border-b border-zinc-200 dark:border-zinc-800 px-6 py-3 flex gap-6 items-center">
          <Link href="/" className="font-semibold">Agent Eval</Link>
          <nav className="flex gap-4 text-sm">
            <Link href="/golden" className="hover:underline">Golden Dataset</Link>
            <Link href="/cases" className="hover:underline">Cases</Link>
            <Link href="/judges" className="hover:underline">Judge Health</Link>
          </nav>
        </header>
        <main className="px-6 py-6 max-w-6xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
