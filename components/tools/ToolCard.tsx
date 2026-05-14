"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tool } from "@/lib/types";
import {
  getSentimentEmoji,
  getSentimentColor,
  getCategoryColor,
  getStarRating,
  formatSentiment,
  normalizeCategory,
} from "@/lib/helpers";

interface ToolCardProps {
  tool: Tool;
}

export function ToolCard({ tool }: ToolCardProps) {
  const sentimentScore = tool.sentimentSummary?.avgSentiment ?? null;
  const avgRating = tool.sentimentSummary?.avgRating ?? null;
  const reviewCount = tool.sentimentSummary?.reviewCount ?? 0;
  const category = normalizeCategory(tool.category);

  // Parse pricing JSON string from API into an object
  const pricing: Record<string, string> =
    typeof tool.pricing === "string"
      ? (() => { try { return JSON.parse(tool.pricing); } catch { return {}; } })()
      : (tool.pricing as Record<string, string>) || {};

  return (
    <Link href={`/tools/${tool.slug}`}>
      <Card className="card-hover group cursor-pointer h-full border-border bg-card">
        <CardContent className="p-5 flex flex-col gap-4 h-full">
          {/* Header: Name + Category Badge */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-1">
              {tool.name}
            </h3>
            <Badge
              variant="outline"
              className={`shrink-0 text-xs ${getCategoryColor(category)}`}
            >
              {category}
            </Badge>
          </div>

          {/* Description */}
          <p className="text-sm text-muted-foreground line-clamp-2 flex-1">
            {tool.description || `AI-powered ${category.toLowerCase()} tool`}
          </p>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-3 pt-2 border-t border-border">
            {/* Sentiment */}
            <div className="flex flex-col items-center gap-1">
              <span className="text-xs text-muted-foreground">Sentiment</span>
              <span className={`text-xl ${getSentimentColor(sentimentScore)}`}>
                {getSentimentEmoji(sentimentScore)}
              </span>
              <span className={`text-xs font-mono ${getSentimentColor(sentimentScore)}`}>
                {sentimentScore !== null ? formatSentiment(sentimentScore) : "—"}
              </span>
            </div>

            {/* Rating */}
            <div className="flex flex-col items-center gap-1">
              <span className="text-xs text-muted-foreground">Rating</span>
              <span className="text-yellow-400 text-sm font-mono">
                {avgRating?.toFixed(1) ?? "—"}
              </span>
              <span className="text-xs text-yellow-400/70 font-mono">
                {avgRating ? getStarRating(avgRating) : "—"}
              </span>
            </div>

            {/* Reviews */}
            <div className="flex flex-col items-center gap-1">
              <span className="text-xs text-muted-foreground">Reviews</span>
              <span className="text-foreground text-lg font-semibold tabular-nums">
                {reviewCount}
              </span>
              <span className="text-xs text-muted-foreground">total</span>
            </div>
          </div>

          {/* Pricing hint */}
          {Object.keys(pricing).length > 0 && (
            <div className="text-xs text-muted-foreground pt-1 border-t border-border/50">
              {Object.entries(pricing)
                .filter(([, v]) => v)
                .slice(0, 2)
                .map(([tier, price]) => (
                  <span key={tier} className="mr-3">
                    <span className="capitalize">{tier}</span>: {price}
                  </span>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
