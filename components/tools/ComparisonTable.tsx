"use client";

import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ToolDetail } from "@/lib/types";
import {
  getSentimentEmoji,
  getSentimentColor,
  formatSentiment,
  getStarRating,
  CHART_COLORS,
} from "@/lib/helpers";

interface ComparisonTableProps {
  tools: ToolDetail[];
}

function DataRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[160px_1fr] border-b border-border/50 last:border-0">
      <div className="p-3 text-sm font-medium text-muted-foreground bg-secondary/30">
        {label}
      </div>
      <div className="grid" style={{ gridTemplateColumns: `repeat(${React.Children.count(children)}, 1fr)` }}>
        {children}
      </div>
    </div>
  );
}

function DataCell({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-3 text-sm text-foreground border-l border-border/50">
      {children}
    </div>
  );
}

export function ComparisonTable({ tools }: ComparisonTableProps) {
  // Pros/cons extracted from reviews (simple extraction)
  const prosCons = useMemo(() => {
    return tools.map((tool) => {
      const positiveReviews = tool.reviews?.filter(
        (r) => r.sentimentLabel === "positive"
      ) || [];
      const negativeReviews = tool.reviews?.filter(
        (r) => r.sentimentLabel === "negative"
      ) || [];

      const findTheme = (reviews: typeof positiveReviews, max: number) =>
        reviews
          .slice(0, max)
          .map((r) => (r.title || r.body).slice(0, 60))
          .filter(Boolean);

      return {
        pros: findTheme(positiveReviews, 3),
        cons: findTheme(negativeReviews, 3),
      };
    });
  }, [tools]);

  return (
    <Card className="border-border bg-card overflow-hidden">
      <CardHeader>
        <CardTitle className="text-lg">Side-by-Side Comparison</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          {/* Tool names header */}
          <div className="grid grid-cols-[160px_1fr] border-b border-border bg-secondary/50">
            <div className="p-3 text-sm font-semibold text-muted-foreground">
              Metric
            </div>
            <div
              className="grid"
              style={{ gridTemplateColumns: `repeat(${tools.length}, 1fr)` }}
            >
              {tools.map((tool) => (
                <div
                  key={tool.id}
                  className="p-3 text-sm font-semibold text-foreground border-l border-border"
                >
                  {tool.name}
                </div>
              ))}
            </div>
          </div>

          {/* Category */}
          <DataRow label="Category">
            {tools.map((tool) => (
              <DataCell key={tool.id}>{tool.category}</DataCell>
            ))}
          </DataRow>

          {/* Pricing */}
          <DataRow label="Starting Price">
            {tools.map((tool) => {
              const pricing = tool.pricing;
              const firstPrice = pricing
                ? Object.entries(pricing).find(
                    ([, v]) => v && v !== "Custom"
                  )
                : null;
              return (
                <DataCell key={tool.id}>
                  {firstPrice
                    ? `${firstPrice[0]}: ${firstPrice[1]}`
                    : "See website"}
                </DataCell>
              );
            })}
          </DataRow>

          {/* Overall Sentiment */}
          <DataRow label="Sentiment">
            {tools.map((tool) => {
              const score = tool.sentimentSummary?.avgSentiment ?? null;
              return (
                <DataCell key={tool.id}>
                  <span className="flex items-center gap-2">
                    <span className={getSentimentColor(score)}>
                      {getSentimentEmoji(score)}
                    </span>
                    <span className={`font-mono ${getSentimentColor(score)}`}>
                      {score !== null ? formatSentiment(score) : "—"}
                    </span>
                  </span>
                </DataCell>
              );
            })}
          </DataRow>

          {/* Rating */}
          <DataRow label="Avg Rating">
            {tools.map((tool) => {
              const rating = tool.sentimentSummary?.avgRating ?? null;
              return (
                <DataCell key={tool.id}>
                  <span className="text-yellow-400 font-mono">
                    {rating?.toFixed(1) || "—"}/5
                  </span>
                  {rating && (
                    <span className="text-xs text-yellow-400/70 ml-1">
                      {getStarRating(rating)}
                    </span>
                  )}
                </DataCell>
              );
            })}
          </DataRow>

          {/* Review Count */}
          <DataRow label="Total Reviews">
            {tools.map((tool) => (
              <DataCell key={tool.id}>
                <span className="font-mono tabular-nums">
                  {tool.sentimentSummary?.reviewCount || 0}
                </span>
              </DataCell>
            ))}
          </DataRow>

          {/* Per-source breakdown */}
          <DataRow label="Reddit Reviews">
            {tools.map((tool) => {
              const rs = tool.sentimentBySource?.find(
                (s) => s.source === "reddit"
              );
              return (
                <DataCell key={tool.id}>
                  <span className="font-mono" style={{ color: CHART_COLORS.reddit }}>
                    {rs?.reviewCount || 0}
                  </span>
                  {rs && (
                    <span className="text-xs text-muted-foreground ml-1">
                      ({formatSentiment(rs.avgSentiment)})
                    </span>
                  )}
                </DataCell>
              );
            })}
          </DataRow>

          <DataRow label="Trustpilot Reviews">
            {tools.map((tool) => {
              const rs = tool.sentimentBySource?.find(
                (s) => s.source === "trustpilot"
              );
              return (
                <DataCell key={tool.id}>
                  <span className="font-mono" style={{ color: CHART_COLORS.trustpilot }}>
                    {rs?.reviewCount || 0}
                  </span>
                  {rs && (
                    <span className="text-xs text-muted-foreground ml-1">
                      ({formatSentiment(rs.avgSentiment)})
                    </span>
                  )}
                </DataCell>
              );
            })}
          </DataRow>

          <DataRow label="G2 Reviews">
            {tools.map((tool) => {
              const rs = tool.sentimentBySource?.find(
                (s) => s.source === "g2"
              );
              return (
                <DataCell key={tool.id}>
                  <span className="font-mono" style={{ color: CHART_COLORS.g2 }}>
                    {rs?.reviewCount || 0}
                  </span>
                  {rs && (
                    <span className="text-xs text-muted-foreground ml-1">
                      ({formatSentiment(rs.avgSentiment)})
                    </span>
                  )}
                </DataCell>
              );
            })}
          </DataRow>

          {/* Positive % */}
          <DataRow label="Positive %">
            {tools.map((tool) => (
              <DataCell key={tool.id}>
                <span className="text-green-400 font-mono">
                  {tool.sentimentSummary?.positivePct || 0}%
                </span>
              </DataCell>
            ))}
          </DataRow>

          {/* Pros (from reviews) */}
          <DataRow label="What users like">
            {prosCons.map((pc, i) => (
              <DataCell key={tools[i].id}>
                {pc.pros.length > 0 ? (
                  <ul className="space-y-1">
                    {pc.pros.map((pro, j) => (
                      <li key={j} className="text-xs text-green-300/80">
                        ✓ {pro}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    No data yet
                  </span>
                )}
              </DataCell>
            ))}
          </DataRow>

          {/* Cons (from reviews) */}
          <DataRow label="Common complaints">
            {prosCons.map((pc, i) => (
              <DataCell key={tools[i].id}>
                {pc.cons.length > 0 ? (
                  <ul className="space-y-1">
                    {pc.cons.map((con, j) => (
                      <li key={j} className="text-xs text-red-300/80">
                        ✗ {con}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    No data yet
                  </span>
                )}
              </DataCell>
            ))}
          </DataRow>
        </div>
      </CardContent>
    </Card>
  );
}
