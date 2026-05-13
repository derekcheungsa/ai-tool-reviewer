import { ToolGrid } from "@/components/tools/ToolGrid";
import { getTools } from "@/lib/api";
import { Tool } from "@/lib/types";

// Revalidate every 5 minutes (ISR)
export const revalidate = 300;

async function getToolsData(): Promise<Tool[]> {
  try {
    return await getTools();
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const tools = await getToolsData();

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      {/* Hero Section */}
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-3">
          <span className="gradient-text">AI Coding Tool</span> Reviews
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Honest, aggregated reviews from Reddit, Trustpilot, and G2. Built for
          non-technical users who want to know which AI tool actually delivers.
        </p>

        {/* Stats Strip */}
        <div className="flex items-center justify-center gap-8 mt-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-green-400" />
            {tools.length} Tools Tracked
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-blue-400" />
            Reddit + Trustpilot + G2
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-purple-400" />
            Updated Weekly
          </div>
        </div>
      </div>

      {/* Tool Grid */}
      {tools.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="animate-pulse-glow mb-6">
            <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center">
              <span className="text-3xl">📡</span>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Waiting for Data
          </h2>
          <p className="text-muted-foreground max-w-md">
            The review database is being populated. Check back soon for
            aggregated reviews across all AI coding tools.
          </p>
        </div>
      ) : (
        <ToolGrid tools={tools} />
      )}
    </div>
  );
}
