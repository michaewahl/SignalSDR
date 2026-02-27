"use client";

import { useState } from "react";
import Link from "next/link";
import { getHeatmapData } from "@/lib/data";
import { CAPABILITY_LABELS, CATEGORY_LABELS, HEATMAP_COLORS, SCORE_LABELS, THREAT_COLORS } from "@/lib/constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { CompetitorCategory, ProductCategory } from "@/lib/types";
import { Search } from "lucide-react";

export default function MatrixPage() {
  const allData = getHeatmapData();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<CompetitorCategory | "all">("all");

  const filtered = allData
    .filter((r) => {
      if (search && !r.name.toLowerCase().includes(search.toLowerCase())) return false;
      if (categoryFilter !== "all" && r.category !== categoryFilter && !r.is_tweddle) return false;
      return true;
    })
    .sort((a, b) => {
      if (a.is_tweddle) return -1;
      if (b.is_tweddle) return 1;
      const aTotal = Object.values(a.scores).reduce((s, v) => s + v, 0);
      const bTotal = Object.values(b.scores).reduce((s, v) => s + v, 0);
      return bTotal - aTotal;
    });

  const dimensions = Object.keys(CAPABILITY_LABELS) as ProductCategory[];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Feature Comparison Matrix</h1>
        <p className="text-sm text-muted-foreground">
          Capability scores across {filtered.length} competitors &middot; 0 (None) to 5 (Market-Leading)
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search competitors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-9"
          />
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => setCategoryFilter("all")}
            className={`rounded-md px-2.5 py-1 text-xs transition-colors ${
              categoryFilter === "all" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"
            }`}
          >
            All
          </button>
          {(Object.keys(CATEGORY_LABELS) as CompetitorCategory[]).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`rounded-md px-2.5 py-1 text-xs transition-colors ${
                categoryFilter === cat ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4">
        <span className="text-xs text-muted-foreground">Score:</span>
        {HEATMAP_COLORS.map((color, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <div className="h-4 w-8 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-[10px] text-muted-foreground">{i} {SCORE_LABELS[i]}</span>
          </div>
        ))}
      </div>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="sticky left-0 z-10 bg-card px-4 py-3 text-left text-xs font-medium text-muted-foreground w-52">
                  Competitor
                </th>
                {dimensions.map((dim) => (
                  <th key={dim} className="px-3 py-3 text-center text-xs font-medium text-muted-foreground min-w-[100px]">
                    {CAPABILITY_LABELS[dim]}
                  </th>
                ))}
                <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground min-w-[60px]">
                  Total
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => {
                const total = Object.values(row.scores).reduce((s, v) => s + v, 0);
                return (
                  <tr
                    key={row.id}
                    className={`border-b border-border/50 transition-colors hover:bg-secondary/50 ${
                      row.is_tweddle ? "bg-accent/5" : ""
                    }`}
                  >
                    <td className={`sticky left-0 z-10 px-4 py-2.5 ${row.is_tweddle ? "bg-accent/5" : "bg-card"}`}>
                      <div className="flex items-center gap-2">
                        {row.is_tweddle && (
                          <div className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse-gold" />
                        )}
                        {row.is_tweddle ? (
                          <span className="text-sm font-bold text-accent">{row.name}</span>
                        ) : (
                          <Link href={`/competitor/${row.id}`} className="text-sm font-medium hover:text-primary transition-colors">
                            {row.name}
                          </Link>
                        )}
                        {!row.is_tweddle && (
                          <Badge
                            variant="outline"
                            className="text-[9px] px-1 py-0"
                            style={{
                              borderColor: THREAT_COLORS[row.threat_level],
                              color: THREAT_COLORS[row.threat_level],
                            }}
                          >
                            {row.threat_level}
                          </Badge>
                        )}
                      </div>
                    </td>
                    {dimensions.map((dim) => {
                      const score = row.scores[dim];
                      return (
                        <td key={dim} className="px-1 py-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div
                                className={`mx-auto flex h-8 w-full items-center justify-center rounded-sm text-xs font-mono font-bold ${
                                  score >= 4 ? "text-primary-foreground" : score >= 2 ? "text-foreground/90" : "text-muted-foreground"
                                }`}
                                style={{ backgroundColor: HEATMAP_COLORS[score] }}
                              >
                                {score}
                              </div>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="font-medium">{row.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {CAPABILITY_LABELS[dim]}: {score}/5 ({SCORE_LABELS[score]})
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </td>
                      );
                    })}
                    <td className="px-3 py-2.5 text-center">
                      <span className={`text-sm font-bold font-mono ${row.is_tweddle ? "text-accent" : ""}`}>
                        {total}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
