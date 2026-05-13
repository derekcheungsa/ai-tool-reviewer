"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { SentimentSummary } from "@/lib/types";
import { CHART_COLORS } from "@/lib/helpers";

interface SentimentDonutProps {
  summary: SentimentSummary | null;
  size?: number;
}

export function SentimentDonut({ summary, size = 200 }: SentimentDonutProps) {
  if (!summary) {
    return (
      <div className="flex items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-sm text-muted-foreground">No data</span>
      </div>
    );
  }

  const data = [
    { name: "Positive", value: Math.round(summary.positivePct), color: CHART_COLORS.positive },
    { name: "Neutral", value: Math.round(summary.neutralPct), color: CHART_COLORS.neutral },
    { name: "Negative", value: Math.round(summary.negativePct), color: CHART_COLORS.negative },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-sm text-muted-foreground">No data</span>
      </div>
    );
  }

  return (
    <div style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={size * 0.22}
            outerRadius={size * 0.38}
            paddingAngle={3}
            dataKey="value"
            stroke="transparent"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #27272a",
              borderRadius: "8px",
              color: "#fafafa",
            }}
            formatter={(value) => [`${value}%`]}
          />
          <Legend
            verticalAlign="bottom"
            height={24}
            formatter={(value: string) => (
              <span className="text-xs text-muted-foreground">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
