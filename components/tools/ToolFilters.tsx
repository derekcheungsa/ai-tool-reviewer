"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CATEGORIES, ToolFilters as ToolFiltersType, SortField } from "@/lib/types";

interface ToolFiltersProps {
  filters: ToolFiltersType;
  onChange: (filters: ToolFiltersType) => void;
}

export function ToolFilters({ filters, onChange }: ToolFiltersProps) {
  const update = (partial: Partial<ToolFiltersType>) => {
    onChange({ ...filters, ...partial });
  };

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <Input
          type="search"
          placeholder="Search tools..."
          value={filters.search}
          onChange={(e) => update({ search: e.target.value })}
          className="bg-secondary border-border text-foreground placeholder:text-muted-foreground"
        />
      </div>

      {/* Filter + Sort row */}
      <div className="flex items-center gap-3">
        {/* Category filter */}
        <Select
          value={filters.category}
          onValueChange={(value) =>
            update({ category: value as ToolFiltersType["category"] })
          }
        >
          <SelectTrigger className="w-[170px] bg-secondary border-border">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent className="bg-secondary border-border">
            <SelectItem value="all">All Categories</SelectItem>
            {CATEGORIES.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Sort */}
        <Select
          value={filters.sort}
          onValueChange={(value) => update({ sort: value as SortField })}
        >
          <SelectTrigger className="w-[150px] bg-secondary border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-secondary border-border">
            <SelectItem value="sentiment">Sentiment</SelectItem>
            <SelectItem value="rating">Rating</SelectItem>
            <SelectItem value="reviewCount">Review Count</SelectItem>
            <SelectItem value="name">Name</SelectItem>
          </SelectContent>
        </Select>

        {/* Sort order */}
        <Select
          value={filters.sortOrder}
          onValueChange={(value) =>
            update({ sortOrder: value as "asc" | "desc" })
          }
        >
          <SelectTrigger className="w-[120px] bg-secondary border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-secondary border-border">
            <SelectItem value="desc">Highest</SelectItem>
            <SelectItem value="asc">Lowest</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
