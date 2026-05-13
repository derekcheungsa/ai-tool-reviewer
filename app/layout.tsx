import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Tool Reviews — Honest Reviews for AI Coding Tools",
  description:
    "Aggregated reviews from Reddit, Trustpilot, and G2 for AI coding tools like Bolt.new, Lovable, Cursor, Replit Agent, and more. Built for non-technical users.",
  keywords: [
    "AI tools",
    "vibe coding",
    "Bolt.new",
    "Lovable",
    "Cursor",
    "Replit Agent",
    "AI app builder",
    "no-code",
    "AI coding",
    "reviews",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
