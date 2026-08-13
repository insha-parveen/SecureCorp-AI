import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

// Type system (CLAUDE.md §25 task #47). Three self-hosted Google families.
// next/font sets a distinct CSS variable per family on <html>; globals.css
// then maps the semantic roles (display / sans / mono) onto these so the
// names never collide with Tailwind's own --font-* theme keys:
//   Space Grotesk  → hero claim + section headers (used with restraint)
//   Inter          → body workhorse
//   JetBrains Mono → every identifier / telemetry token
// `display: swap` avoids invisible-text flashes; next/font eliminates layout
// shift by reserving metrics up front.
const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const sans = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "NexaCore AI",
  description: "SecureCorp AI — secure enterprise HybridRAG assistant.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
    >
      <body className="min-h-dvh antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}