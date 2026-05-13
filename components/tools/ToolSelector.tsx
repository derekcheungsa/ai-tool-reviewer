"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { searchTools } from "@/lib/api";
import { Tool } from "@/lib/types";
import { normalizeCategory } from "@/lib/helpers";

interface ToolSelectorProps {
  selected: string[];
  onChange: (slugs: string[]) => void;
}

export function ToolSelector({ selected, onChange }: ToolSelectorProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  const searchFn = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const tools = await searchTools(q);
      setResults(tools.filter((t) => !selected.includes(t.slug)));
    } catch {
      setResults([]);
    }
    setLoading(false);
  }, [selected]);

  useEffect(() => {
    const timer = setTimeout(() => searchFn(query), 300);
    return () => clearTimeout(timer);
  }, [query, searchFn]);

  const addTool = (slug: string) => {
    if (selected.length >= 4) return;
    const newSelected = [...selected, slug];
    onChange(newSelected);
    const params = new URLSearchParams(searchParams.toString());
    params.set("tools", newSelected.join(","));
    router.push(`/compare?${params.toString()}`, { scroll: false });
    setOpen(false);
    setQuery("");
  };

  const removeTool = (slug: string) => {
    const newSelected = selected.filter((s) => s !== slug);
    onChange(newSelected);
    if (newSelected.length > 0) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("tools", newSelected.join(","));
      router.push(`/compare?${params.toString()}`, { scroll: false });
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {selected.map((slug) => (
        <Badge
          key={slug}
          variant="secondary"
          className="px-3 py-1.5 text-sm cursor-pointer hover:bg-destructive/20"
          onClick={() => removeTool(slug)}
        >
          {slug.replace(/-/g, " ")} ✕
        </Badge>
      ))}

      {selected.length < 4 && (
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger>
            <Button variant="outline" size="sm" className="border-dashed">
              + Add Tool ({selected.length}/4)
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card border-border max-w-md">
            <DialogHeader>
              <DialogTitle className="text-foreground">
                Add Tool to Compare
              </DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-3 mt-2">
              <Input
                type="search"
                placeholder="Search tools..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="bg-secondary border-border"
                autoFocus
              />
              {loading && (
                <div className="text-sm text-muted-foreground animate-pulse">
                  Searching...
                </div>
              )}
              {results.length > 0 && (
                <div className="flex flex-col gap-1 max-h-64 overflow-y-auto">
                  {results.map((tool) => (
                    <button
                      key={tool.slug}
                      onClick={() => addTool(tool.slug)}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary transition-colors text-left"
                    >
                      <div>
                        <div className="text-sm font-medium text-foreground">
                          {tool.name}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {normalizeCategory(tool.category)}
                        </div>
                      </div>
                      <span className="text-lg text-muted-foreground">+</span>
                    </button>
                  ))}
                </div>
              )}
              {!loading && query.length >= 2 && results.length === 0 && (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No tools found for &quot;{query}&quot;
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
