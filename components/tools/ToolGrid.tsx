"use client";

import { useState, useMemo } from "react";
import { ToolCard } from "./ToolCard";
import { ToolFilters } from "./ToolFilters";
import { Tool, ToolFilters as ToolFiltersType } from "@/lib/types";
import { normalizeCategory } from "@/lib/helpers";

interface ToolGridProps {
  tools: Tool[];
}

export function ToolGrid({ tools }: ToolGridProps) {
  const [filters, setFilters] = useState<ToolFiltersType>({
    search: "",
    category: "all",
    sort: "sentiment",
    sortOrder: "desc",
  });

  const filtered = useMemo(() => {
    let result = [...tools];

    // Search filter
    if (filters.search.trim()) {
      const query = filters.search.toLowerCase();
      result = result.filter(
        (t) =>
          t.name.toLowerCase().includes(query) ||
          (t.description && t.description.toLowerCase().includes(query)) ||
          normalizeCategory(t.category).toLowerCase().includes(query)
      );
    }

    // Category filter
    if (filters.category !== "all") {
      result = result.filter(
        (t) => normalizeCategory(t.category) === filters.category
      );
    }

    // Sort
    result.sort((a, b) => {
      let aVal: number, bVal: number;
      switch (filters.sort) {
        case "sentiment":
          aVal = a.sentimentSummary?.avgSentiment ?? -1;
          bVal = b.sentimentSummary?.avgSentiment ?? -1;
          break;
        case "rating":
          aVal = a.sentimentSummary?.avgRating ?? 0;
          bVal = b.sentimentSummary?.avgRating ?? 0;
          break;
        case "reviewCount":
          aVal = a.sentimentSummary?.reviewCount ?? 0;
          bVal = b.sentimentSummary?.reviewCount ?? 0;
          break;
        case "name":
          return filters.sortOrder === "asc"
            ? a.name.localeCompare(b.name)
            : b.name.localeCompare(a.name);
        default:
          return 0;
      }
      return filters.sortOrder === "desc" ? bVal - aVal : aVal - bVal;
    });

    return result;
  }, [tools, filters]);

  return (
    <div className="flex flex-col gap-6">
      <ToolFilters filters={filters} onChange={setFilters} />

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-5xl mb-4">🔍</span>
          <h3 className="text-lg font-medium text-foreground mb-1">
            No tools found
          </h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Try adjusting your search or filters to find what you&apos;re
            looking for.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            Showing {filtered.length} of {tools.length} tools
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((tool) => (
              <ToolCard key={tool.id} tool={tool} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
