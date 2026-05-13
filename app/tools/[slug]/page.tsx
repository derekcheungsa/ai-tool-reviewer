import { notFound } from "next/navigation";
import { ToolDetailClient } from "@/components/reviews/ToolDetailClient";
import { getToolDetail } from "@/lib/api";
import { ToolDetail } from "@/lib/types";

export const revalidate = 300;

interface ToolPageProps {
  params: Promise<{ slug: string }>;
}

async function getToolData(slug: string): Promise<ToolDetail | null> {
  try {
    return await getToolDetail(slug);
  } catch {
    return null;
  }
}

export default async function ToolPage({ params }: ToolPageProps) {
  const { slug } = await params;
  const tool = await getToolData(slug);

  if (!tool) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-20 text-center">
        <div className="mb-6">
          <span className="text-6xl">🔧</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          Tool Not Found
        </h1>
        <p className="text-muted-foreground max-w-md mx-auto">
          We couldn&apos;t find a tool matching &quot;{slug}&quot;. It may not
          be in our catalog yet, or the slug may be incorrect.
        </p>
        <a
          href="/"
          className="inline-block mt-6 text-sm text-primary hover:text-primary/80 transition-colors"
        >
          ← Back to all tools
        </a>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-muted-foreground">
        <a href="/" className="hover:text-foreground transition-colors">
          Tools
        </a>
        <span className="mx-2">/</span>
        <span className="text-foreground">{tool.name}</span>
      </nav>

      <ToolDetailClient tool={tool} />
    </div>
  );
}
