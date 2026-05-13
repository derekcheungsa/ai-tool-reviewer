"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { SentimentDonut } from "./SentimentDonut";
import { ToolDetail } from "@/lib/types";
import { CHART_COLORS } from "@/lib/helpers";

interface ComparisonChartsProps {
  tools: ToolDetail[];
}

export function ComparisonCharts({ tools }: ComparisonChartsProps) {
  // Bar chart: side-by-side sentiment scores per source
  const barData = [
    { source: "Reddit", ...Object.fromEntries(tools.map((t, i) => {
      const s = t.sentimentBySource?.find((x) => x.source === "reddit");
      return [t.name, s ? Math.round(((s.avgSentiment + 1) / 2) * 100) : 0];
    })) },
    { source: "Trustpilot", ...Object.fromEntries(tools.map((t, i) => {
      const s = t.sentimentBySource?.find((x) => x.source === "trustpilot");
      return [t.name, s ? Math.round(((s.avgSentiment + 1) / 2) * 100) : 0];
    })) },
    { source: "G2", ...Object.fromEntries(tools.map((t, i) => {
      const s = t.sentimentBySource?.find((x) => x.source === "g2");
      return [t.name, s ? Math.round(((s.avgSentiment + 1) / 2) * 100) : 0];
    })) },
  ];

  const barColors = [CHART_COLORS.primary, CHART_COLORS.secondary, "#22c55e", "#eab308"];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Sentiment Bar Chart */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-lg">Sentiment by Source</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={barData}
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
                <Legend
                  formatter={(value: string) => (
                    <span className="text-xs text-muted-foreground">{value}</span>
                  )}
                />
                {tools.map((tool, i) => (
                  <Bar
                    key={tool.id}
                    dataKey={tool.name}
                    fill={barColors[i % barColors.length]}
                    radius={[4, 4, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Donuts: one per tool */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-lg">Sentiment Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center justify-center gap-6">
            {tools.map((tool) => (
              <div key={tool.id} className="flex flex-col items-center gap-2">
                <SentimentDonut summary={tool.sentimentSummary || null} size={160} />
                <span className="text-sm font-medium text-foreground">
                  {tool.name}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
