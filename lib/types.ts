// Types for the AI Tool Review Aggregator

export interface ToolPricing {
  free?: string;
  [key: string]: string | undefined;
}

export interface Tool {
  id: string;
  name: string;
  slug: string;
  website: string;
  description: string;
  category: string;
  pricing: ToolPricing;
  targetUser: string;
  launchDate: string;
  maturity: string;
  createdAt: string;

  // Aggregated sentiment summary (joined from API)
  sentimentSummary?: SentimentSummary;
}

export interface SentimentSummary {
  id: string;
  toolId: string;
  source: string;
  avgRating: number;
  avgSentiment: number;
  positivePct: number;
  neutralPct: number;
  negativePct: number;
  reviewCount: number;
  updatedAt: string;

  // Per-source breakdowns (for tool detail page)
  perSource?: PerSourceSentiment[];
}

export interface PerSourceSentiment {
  source: "reddit" | "trustpilot" | "g2";
  avgRating: number;
  avgSentiment: number;
  positivePct: number;
  neutralPct: number;
  negativePct: number;
  reviewCount: number;
}

export interface Review {
  id: string;
  toolId: string;
  source: "reddit" | "trustpilot" | "g2";
  sourceUrl: string | null;
  authorName: string | null;
  authorRole: string | null;
  title: string | null;
  body: string;
  rating: number | null;
  sentimentScore: number | null;
  sentimentLabel: "positive" | "negative" | "neutral" | "mixed" | null;
  publishedAt: string | null;
  scrapedAt: string;
}

export interface ToolDetail extends Tool {
  reviews: Review[];
  sentimentBySource: PerSourceSentiment[];
}

export interface CompareData {
  tools: ToolDetail[];
}

export interface Stats {
  totalTools: number;
  totalReviews: number;
  avgSentiment: number;
  topTools: Tool[];
  sourcesBreakdown: {
    reddit: number;
    trustpilot: number;
    g2: number;
  };
}

export type Category =
  | "App Builders"
  | "Code Editors"
  | "CLI Agents"
  | "Autonomous Agents"
  | "Traditional No-Code";

export const CATEGORIES: Category[] = [
  "App Builders",
  "Code Editors",
  "CLI Agents",
  "Autonomous Agents",
  "Traditional No-Code",
];

export const CATEGORY_LABELS: Record<string, string> = {
  "App Builders": "App Builders",
  "Code Editors": "Code Editors",
  "CLI Agents": "CLI Agents",
  "Autonomous Agents": "Autonomous Agents",
  "Traditional No-Code": "Traditional No-Code",
};

export type SortField = "name" | "sentiment" | "rating" | "reviewCount";
export type SortOrder = "asc" | "desc";

export interface ToolFilters {
  search: string;
  category: Category | "all";
  sort: SortField;
  sortOrder: SortOrder;
}

export type SentimentLabel = "positive" | "negative" | "neutral" | "mixed";
export type ReviewSource = "reddit" | "trustpilot" | "g2" | "all";

export interface ReviewFilters {
  source: ReviewSource;
  sentiment: SentimentLabel | "all";
  dateFrom: string;
  dateTo: string;
}

// Source display metadata
export const SOURCE_CONFIG: Record<string, {
  label: string;
  icon: string;
  color: string;
  url: string;
}> = {
  reddit: {
    label: "Reddit",
    icon: "🔴",
    color: "#FF4500",
    url: "https://reddit.com",
  },
  trustpilot: {
    label: "Trustpilot",
    icon: "⭐",
    color: "#00B67A",
    url: "https://trustpilot.com",
  },
  g2: {
    label: "G2",
    icon: "📊",
    color: "#FF492C",
    url: "https://g2.com",
  },
};
