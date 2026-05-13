import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold text-white">
              AI
            </div>
            <span className="text-sm text-muted-foreground">
              AI Tool Reviews — Aggregated honest reviews from Reddit, Trustpilot & G2
            </span>
          </div>

          <nav className="flex items-center gap-4 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-foreground transition-colors">
              Home
            </Link>
            <Link href="/compare" className="hover:text-foreground transition-colors">
              Compare
            </Link>
            <span className="text-border">|</span>
            <span>&copy; {new Date().getFullYear()}</span>
          </nav>
        </div>
      </div>
    </footer>
  );
}
