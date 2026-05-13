"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ReviewFilters as ReviewFiltersType } from "@/lib/types";

interface ReviewFiltersProps {
  filters: ReviewFiltersType;
  onChange: (filters: ReviewFiltersType) => void;
}

export function ReviewFilters({ filters, onChange }: ReviewFiltersProps) {
  const update = (partial: Partial<ReviewFiltersType>) => {
    onChange({ ...filters, ...partial });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Select
        value={filters.source}
        onValueChange={(v) => update({ source: v as ReviewFiltersType["source"] })}
      >
        <SelectTrigger className="w-[140px] bg-secondary border-border text-sm">
          <SelectValue placeholder="All Sources" />
        </SelectTrigger>
        <SelectContent className="bg-secondary border-border">
          <SelectItem value="all">All Sources</SelectItem>
          <SelectItem value="reddit">🔴 Reddit</SelectItem>
          <SelectItem value="trustpilot">⭐ Trustpilot</SelectItem>
          <SelectItem value="g2">📊 G2</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.sentiment}
        onValueChange={(v) =>
          update({ sentiment: v as ReviewFiltersType["sentiment"] })
        }
      >
        <SelectTrigger className="w-[140px] bg-secondary border-border text-sm">
          <SelectValue placeholder="All Sentiments" />
        </SelectTrigger>
        <SelectContent className="bg-secondary border-border">
          <SelectItem value="all">All Sentiments</SelectItem>
          <SelectItem value="positive">😊 Positive</SelectItem>
          <SelectItem value="neutral">😐 Neutral</SelectItem>
          <SelectItem value="mixed">🤔 Mixed</SelectItem>
          <SelectItem value="negative">😞 Negative</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

// Sort options for reviews
export function ReviewSort({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <Select value={value} onValueChange={(v) => v && onChange(v)}>
      <SelectTrigger className="w-[160px] bg-secondary border-border text-sm">
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="bg-secondary border-border">
        <SelectItem value="recent">Most Recent</SelectItem>
        <SelectItem value="oldest">Oldest First</SelectItem>
        <SelectItem value="highest">Highest Rating</SelectItem>
        <SelectItem value="lowest">Lowest Rating</SelectItem>
        <SelectItem value="positive">Most Positive</SelectItem>
        <SelectItem value="negative">Most Negative</SelectItem>
      </SelectContent>
    </Select>
  );
}
