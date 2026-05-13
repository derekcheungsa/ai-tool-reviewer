import { Tool, ToolDetail, CompareData, Stats, ReviewFilters } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }

  return res.json();
}

// GET /api/tools — list all tools with optional filters
export async function getTools(params?: {
  search?: string;
  category?: string;
  sort?: string;
  order?: string;
}): Promise<Tool[]> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set("search", params.search);
  if (params?.category && params.category !== "all") searchParams.set("category", params.category);
  if (params?.sort) searchParams.set("sort", params.sort);
  if (params?.order) searchParams.set("order", params.order);

  const query = searchParams.toString();
  return fetchAPI<Tool[]>(`/api/tools${query ? `?${query}` : ""}`);
}

// GET /api/tools/[slug] — tool detail with reviews
export async function getToolDetail(
  slug: string,
  reviewFilters?: ReviewFilters
): Promise<ToolDetail> {
  const searchParams = new URLSearchParams();
  if (reviewFilters?.source && reviewFilters.source !== "all")
    searchParams.set("source", reviewFilters.source);
  if (reviewFilters?.sentiment && reviewFilters.sentiment !== "all")
    searchParams.set("sentiment", reviewFilters.sentiment);
  if (reviewFilters?.dateFrom) searchParams.set("dateFrom", reviewFilters.dateFrom);
  if (reviewFilters?.dateTo) searchParams.set("dateTo", reviewFilters.dateTo);

  const query = searchParams.toString();
  return fetchAPI<ToolDetail>(`/api/tools/${slug}${query ? `?${query}` : ""}`);
}

// GET /api/compare?tools=slug1,slug2,slug3
export async function getCompareData(slugs: string[]): Promise<CompareData> {
  return fetchAPI<CompareData>(`/api/compare?tools=${slugs.join(",")}`);
}

// GET /api/stats — aggregate statistics
export async function getStats(): Promise<Stats> {
  return fetchAPI<Stats>("/api/stats");
}

// GET /api/tools — search tools by name (for compare selector)
export async function searchTools(query: string): Promise<Tool[]> {
  return fetchAPI<Tool[]>(`/api/tools?search=${encodeURIComponent(query)}&limit=20`);
}
