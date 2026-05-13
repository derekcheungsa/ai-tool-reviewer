"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { ToolSelector } from "./ToolSelector";
import { ComparisonTable } from "./ComparisonTable";
import { ComparisonCharts } from "@/components/charts/ComparisonCharts";
import { getCompareData } from "@/lib/api";
import { ToolDetail } from "@/lib/types";

export function CompareClient() {
  const searchParams = useSearchParams();
  const toolsParam = searchParams.get("tools");
  const [selected, setSelected] = useState<string[]>(
    toolsParam ? toolsParam.split(",").slice(0, 4) : []
  );
  const [tools, setTools] = useState<ToolDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = useCallback(async (slugs: string[]) => {
    if (slugs.length < 2) {
      setTools([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await getCompareData(slugs);
      setTools(data.tools || []);
    } catch (err) {
      setError("Failed to load comparison data. Please try again.");
      setTools([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchComparison(selected);
  }, [selected, fetchComparison]);

  return (
    <div className="flex flex-col gap-8">
      {/* Tool Selector */}
      <div>
        <label className="text-sm font-medium text-muted-foreground block mb-2">
          Select tools to compare (2–4)
        </label>
        <ToolSelector selected={selected} onChange={setSelected} />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-pulse-glow">
              <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center">
                <span className="text-2xl">⚖️</span>
              </div>
            </div>
            <p className="text-muted-foreground">Loading comparison data...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-5xl mb-4">⚠️</span>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Error Loading Data
          </h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={() => fetchComparison(selected)}
            className="text-sm text-primary hover:text-primary/80 transition-colors"
          >
            Try again →
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && tools.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-border rounded-xl">
          <span className="text-6xl mb-4">🔀</span>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Select Tools to Compare
          </h2>
          <p className="text-muted-foreground max-w-md">
            Add 2–4 tools using the selector above to see a detailed
            side-by-side comparison including sentiment scores, pricing, and
            reviews.
          </p>
        </div>
      )}

      {/* Comparison Content */}
      {!loading && !error && tools.length >= 2 && (
        <>
          <ComparisonTable tools={tools} />
          <ComparisonCharts tools={tools} />
        </>
      )}
    </div>
  );
}
