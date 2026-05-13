import { Suspense } from "react";
import { CompareClient } from "@/components/tools/CompareClient";

export const revalidate = 300;

export default function ComparePage() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          <span className="gradient-text">Compare</span> AI Coding Tools
        </h1>
        <p className="text-muted-foreground max-w-2xl">
          Select 2–4 tools to compare side-by-side. See how they stack up on
          sentiment, pricing, ratings, and real user feedback.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse-glow text-muted-foreground">
              Loading comparison...
            </div>
          </div>
        }
      >
        <CompareClient />
      </Suspense>
    </div>
  );
}
