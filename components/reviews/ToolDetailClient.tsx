"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ReviewCard } from "./ReviewCard";
import { ReviewFilters, ReviewSort } from "./ReviewFilters";
import { SentimentBarChart } from "../charts/SentimentBarChart";
import { SentimentDonut } from "../charts/SentimentDonut";
import { Review, ToolDetail, ReviewFilters as ReviewFiltersType, SOURCE_CONFIG } from "@/lib/types";
import {
  getCategoryColor,
  getSentimentEmoji,
  getSentimentColor,
  formatSentiment,
  normalizeCategory,
} from "@/lib/helpers";

interface ToolDetailClientProps {
  tool: ToolDetail;
}

export function ToolDetailClient({ tool }: ToolDetailClientProps) {
  const [reviewFilters, setReviewFilters] = useState<ReviewFiltersType>({
    source: "all",
    sentiment: "all",
    dateFrom: "",
    dateTo: "",
  });
  const [sortBy, setSortBy] = useState("recent");

  const filteredReviews = useMemo(() => {
    let reviews = [...(tool.reviews || [])];

    // Source filter
    if (reviewFilters.source !== "all") {
      reviews = reviews.filter((r) => r.source === reviewFilters.source);
    }

    // Sentiment filter
    if (reviewFilters.sentiment !== "all") {
      reviews = reviews.filter(
        (r) => r.sentimentLabel === reviewFilters.sentiment
      );
    }

    // Sort
    reviews.sort((a, b) => {
      switch (sortBy) {
        case "recent":
          return (
            new Date(b.publishedAt || 0).getTime() -
            new Date(a.publishedAt || 0).getTime()
          );
        case "oldest":
          return (
            new Date(a.publishedAt || 0).getTime() -
            new Date(b.publishedAt || 0).getTime()
          );
        case "highest":
          return (b.rating || 0) - (a.rating || 0);
        case "lowest":
          return (a.rating || 0) - (b.rating || 0);
        case "positive":
          return (b.sentimentScore || 0) - (a.sentimentScore || 0);
        case "negative":
          return (a.sentimentScore || 0) - (b.sentimentScore || 0);
        default:
          return 0;
      }
    });

    return reviews;
  }, [tool.reviews, reviewFilters, sortBy]);

  const category = normalizeCategory(tool.category);
  const summary = tool.sentimentSummary || null;
  const sentimentScore = summary?.avgSentiment ?? null;
  const bySource = tool.sentimentBySource || [];

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <Badge variant="outline" className={getCategoryColor(category)}>
            {category}
          </Badge>
          {tool.website && (
            <a
              href={tool.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:text-primary/80 transition-colors"
            >
              {tool.website.replace(/^https?:\/\//, "")} ↗
            </a>
          )}
        </div>

        <h1 className="text-3xl font-bold tracking-tight mb-2">{tool.name}</h1>

        {tool.description && (
          <p className="text-muted-foreground max-w-3xl">{tool.description}</p>
        )}

        {/* Pricing */}
        {tool.pricing && (
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(tool.pricing)
              .filter(([, v]) => v)
              .map(([tier, price]) => (
                <Badge
                  key={tier}
                  variant="secondary"
                  className="text-xs capitalize"
                >
                  {tier}: {price}
                </Badge>
              ))}
          </div>
        )}
      </div>

      {/* Sentiment Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Overall Score */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Overall Sentiment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <span className={`text-4xl ${getSentimentColor(sentimentScore)}`}>
                {getSentimentEmoji(sentimentScore)}
              </span>
              <div>
                <div className={`text-2xl font-bold ${getSentimentColor(sentimentScore)}`}>
                  {sentimentScore !== null ? formatSentiment(sentimentScore) : "—"}
                </div>
                <div className="text-xs text-muted-foreground">
                  {summary?.reviewCount || 0} reviews
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Rating */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Average Rating
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <span className="text-4xl">⭐</span>
              <div>
                <div className="text-2xl font-bold text-yellow-400">
                  {summary?.avgRating?.toFixed(1) || "—"}
                  <span className="text-sm text-muted-foreground font-normal">
                    /5
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {summary?.avgRating
                    ? `${summary.positivePct}% positive`
                    : "No ratings yet"}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Review Count */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Review Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-1.5">
              {bySource.map((s) => (
                <div key={s.source} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground flex items-center gap-1.5">
                    <span>{SOURCE_CONFIG[s.source]?.icon}</span>
                    {SOURCE_CONFIG[s.source]?.label || s.source}
                  </span>
                  <span className="font-mono tabular-nums text-foreground">
                    {s.reviewCount} reviews
                  </span>
                </div>
              ))}
              {bySource.length === 0 && (
                <span className="text-sm text-muted-foreground">No data yet</span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bar Chart: Per-source sentiment */}
        <Card className="border-border bg-card lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Sentiment by Source</CardTitle>
          </CardHeader>
          <CardContent>
            {bySource.length > 0 ? (
              <SentimentBarChart data={bySource} />
            ) : (
              <div className="flex items-center justify-center h-64 text-muted-foreground">
                No per-source data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Donut: Sentiment Distribution */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Distribution</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
            <SentimentDonut summary={summary} size={220} />
          </CardContent>
        </Card>
      </div>

      {/* Reviews Section */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <h2 className="text-xl font-semibold">
            Reviews
            <span className="text-sm font-normal text-muted-foreground ml-2">
              ({filteredReviews.length})
            </span>
          </h2>
          <div className="flex items-center gap-3">
            <ReviewFilters
              filters={reviewFilters}
              onChange={setReviewFilters}
            />
            <ReviewSort value={sortBy} onChange={setSortBy} />
          </div>
        </div>

        {filteredReviews.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center border border-border rounded-lg">
            <span className="text-4xl mb-3">📝</span>
            <h3 className="text-lg font-medium text-foreground mb-1">
              No reviews found
            </h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              {tool.reviews?.length
                ? "Try adjusting your filters to see more reviews."
                : "Reviews are being collected. Check back soon."}
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {filteredReviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
