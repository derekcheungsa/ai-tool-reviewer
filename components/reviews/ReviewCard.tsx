"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Review, SOURCE_CONFIG } from "@/lib/types";
import {
  getSentimentBadgeColor,
  getStarRating,
  formatDate,
  truncate,
} from "@/lib/helpers";

interface ReviewCardProps {
  review: Review;
}

export function ReviewCard({ review }: ReviewCardProps) {
  const sourceConfig = SOURCE_CONFIG[review.source];
  const sentimentColor = getSentimentBadgeColor(review.sentimentLabel || undefined);

  return (
    <Card className="border-border bg-card hover:border-muted-foreground/30 transition-colors">
      <CardContent className="p-4 flex flex-col gap-3">
        {/* Header: Source + Sentiment + Rating */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-lg" title={sourceConfig.label}>
              {sourceConfig.icon}
            </span>
            <span className="text-xs font-medium text-muted-foreground">
              {sourceConfig.label}
            </span>
            {review.authorName && (
              <>
                <span className="text-border">·</span>
                <span className="text-xs text-muted-foreground">
                  {review.authorName}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            {review.sentimentLabel && (
              <Badge variant="outline" className={`text-xs ${sentimentColor}`}>
                {review.sentimentLabel}
              </Badge>
            )}
            {review.rating && (
              <span className="text-yellow-400 text-xs font-mono">
                {getStarRating(review.rating)} {review.rating.toFixed(0)}/5
              </span>
            )}
          </div>
        </div>

        {/* Title */}
        {review.title && (
          <h4 className="text-sm font-medium text-foreground">
            {review.title}
          </h4>
        )}

        {/* Body excerpt */}
        <p className="text-sm text-muted-foreground leading-relaxed">
          {truncate(review.body, 300)}
        </p>

        {/* Footer: Date + Link */}
        <div className="flex items-center justify-between pt-1 border-t border-border/50">
          <span className="text-xs text-muted-foreground">
            {formatDate(review.publishedAt)}
            {review.authorRole && (
              <span className="ml-2 text-muted-foreground/70">
                · {review.authorRole}
              </span>
            )}
          </span>
          {review.sourceUrl && (
            <a
              href={review.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary hover:text-primary/80 transition-colors"
            >
              View original →
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
