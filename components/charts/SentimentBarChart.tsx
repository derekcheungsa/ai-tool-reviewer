"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { PerSourceSentiment } from "@/lib/types";
import { CHART_COLORS } from "@/lib/helpers";

interface SentimentBarChartProps {
  data: PerSourceSentiment[];
}

export function SentimentBarChart({ data }: SentimentBarChartProps) {
  const chartData = data.map((d) => ({
    source: d.source.charAt(0).toUpperCase() + d.source.slice(1),
    sentiment: Math.round(((d.avgSentiment + 1) / 2) * 100),
    rating: d.avgRating ? (d.avgRating / 5) * 100 : 0,
    reviews: d.reviewCount,
    color: d.source === "reddit"
      ? CHART_COLORS.reddit
      : d.source === "trustpilot"
        ? CHART_COLORS.trustpilot
        : CHART_COLORS.g2,
  }));

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 10, left: -10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="source"
            tick={{ fill: "#a1a1aa", fontSize: 12 }}
            axisLine={{ stroke: "#27272a" }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#a1a1aa", fontSize: 12 }}
            axisLine={{ stroke: "#27272a" }}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #27272a",
              borderRadius: "8px",
              color: "#fafafa",
            }}
            formatter={(value) => [`${value}%`]}
          />
          <Bar dataKey="sentiment" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
