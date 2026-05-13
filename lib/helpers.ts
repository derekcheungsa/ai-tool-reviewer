import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { SentimentLabel, Tool, CATEGORIES } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format a sentiment score (-1 to 1) to display percentage
export function formatSentiment(score: number): string {
  const pct = Math.round(((score + 1) / 2) * 100);
  return `${pct}%`;
}

// Get sentiment emoji for display
export function getSentimentEmoji(score: number | null): string {
  if (score === null) return "➖";
  if (score > 0.3) return "😊";
  if (score > 0) return "🙂";
  if (score === 0) return "😐";
  if (score > -0.3) return "🙁";
  return "😞";
}

// Get sentiment color class
export function getSentimentColor(score: number | null): string {
  if (score === null) return "text-gray-400";
  if (score > 0.3) return "text-green-400";
  if (score > 0) return "text-green-300";
  if (score === 0) return "text-yellow-400";
  if (score > -0.3) return "text-orange-400";
  return "text-red-400";
}

// Get sentiment bg color for badges
export function getSentimentBadgeColor(label: SentimentLabel | null | undefined): string {
  switch (label) {
    case "positive":
      return "bg-green-900/50 text-green-300 border-green-700";
    case "negative":
      return "bg-red-900/50 text-red-300 border-red-700";
    case "neutral":
      return "bg-gray-800 text-gray-300 border-gray-600";
    case "mixed":
      return "bg-yellow-900/50 text-yellow-300 border-yellow-700";
    default:
      return "bg-gray-800 text-gray-400 border-gray-600";
  }
}

// Format a date string for display
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Unknown";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

// Get relative time string
export function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
  return `${Math.floor(diffDays / 365)}y ago`;
}

// Truncate text
export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).trim() + "...";
}

// Get category badge color
export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    "App Builders": "bg-blue-900/50 text-blue-300 border-blue-700",
    "Code Editors": "bg-purple-900/50 text-purple-300 border-purple-700",
    "CLI Agents": "bg-amber-900/50 text-amber-300 border-amber-700",
    "Autonomous Agents": "bg-rose-900/50 text-rose-300 border-rose-700",
    "Traditional No-Code": "bg-teal-900/50 text-teal-300 border-teal-700",
  };
  return colors[category] || "bg-gray-800 text-gray-300 border-gray-600";
}

// Generate star rating display (1-5)
export function getStarRating(rating: number | null): string {
  if (rating === null) return "☆☆☆☆☆";
  const full = Math.round(rating);
  return "★".repeat(full) + "☆".repeat(5 - full);
}

// Normalize category from API to display category
export function normalizeCategory(cat: string): string {
  const map: Record<string, string> = {
    app_builders: "App Builders",
    code_editors: "Code Editors",
    cli_agents: "CLI Agents",
    autonomous_agents: "Autonomous Agents",
    traditional_nocode: "Traditional No-Code",
    "app builders": "App Builders",
    "code editors": "Code Editors",
    "cli agents": "CLI Agents",
    "autonomous agents": "Autonomous Agents",
    "traditional no-code": "Traditional No-Code",
  };
  return map[cat] || cat;
}

// Get all tool slugs for compare page
export function getAllSlugs(tools: Tool[]): { value: string; label: string }[] {
  return tools.map((t) => ({ value: t.slug, label: t.name }));
}

// Color palette for charts
export const CHART_COLORS = {
  positive: "#22c55e",
  neutral: "#eab308",
  negative: "#ef4444",
  mixed: "#f97316",
  reddit: "#FF4500",
  trustpilot: "#00B67A",
  g2: "#FF492C",
  primary: "#3b82f6",
  secondary: "#8b5cf6",
};
