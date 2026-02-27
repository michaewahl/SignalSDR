"use client";

import { useState } from "react";
import Link from "next/link";
import { getByCategory, getSelf } from "@/lib/data";
import { getShortName } from "@/lib/company";
import { CATEGORY_LABELS, CATEGORY_COLORS, CAPABILITY_LABELS, THREAT_COLORS, HEATMAP_COLORS } from "@/lib/constants";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { CompetitorCategory, ProductCategory } from "@/lib/types";

export default function CategoriesPage() {
  const categories = Object.keys(CATEGORY_LABELS) as CompetitorCategory[];
  const self = getSelf();
  const shortName = getShortName();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Category Breakdown</h1>
        <p className="text-sm text-muted-foreground">
          Competitors grouped by primary product category
        </p>
      </div>

      <Tabs defaultValue={categories[0]}>
        <TabsList className="bg-secondary">
          {categories.map((cat) => (
            <TabsTrigger key={cat} value={cat} className="text-xs">
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full" style={{ background: CATEGORY_COLORS[cat] }} />
                {CATEGORY_LABELS[cat]}
              </div>
            </TabsTrigger>
          ))}
        </TabsList>

        {categories.map((cat) => {
          const competitors = getByCategory(cat).sort((a, b) => b.threat_score - a.threat_score);
          return (
            <TabsContent key={cat} value={cat} className="space-y-3 mt-4">
              <p className="text-sm text-muted-foreground">{competitors.length} competitors in this category</p>
              {competitors.map((c) => (
                <Card key={c.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Link href={`/competitor/${c.id}`} className="text-sm font-bold hover:text-primary transition-colors">
                            {c.name}
                          </Link>
                          {c.parent_company && (
                            <span className="text-xs text-muted-foreground">({c.parent_company})</span>
                          )}
                          <Badge
                            variant="outline"
                            className="text-[10px] px-1.5 py-0"
                            style={{ borderColor: THREAT_COLORS[c.threat_level], color: THREAT_COLORS[c.threat_level] }}
                          >
                            {c.threat_level} ({c.threat_score})
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground max-w-xl">{c.description}</p>
                      </div>
                      <div className="text-right text-xs text-muted-foreground space-y-0.5">
                        {c.headquarters && <p>{c.headquarters}</p>}
                        {c.employees_approx && <p>{c.employees_approx} employees</p>}
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-5 gap-2">
                      {(Object.keys(CAPABILITY_LABELS) as ProductCategory[]).map((dim) => {
                        const score = c.capabilities[dim];
                        const selfScore = self.capabilities[dim];
                        return (
                          <div key={dim} className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] text-muted-foreground">{CAPABILITY_LABELS[dim]}</span>
                              <span className="text-[10px] font-mono font-bold" style={{ color: HEATMAP_COLORS[score] }}>
                                {score}
                              </span>
                            </div>
                            <div className="flex gap-0.5">
                              {[1, 2, 3, 4, 5].map((n) => (
                                <div
                                  key={n}
                                  className="h-1.5 flex-1 rounded-full"
                                  style={{
                                    backgroundColor: n <= score ? HEATMAP_COLORS[score] : "oklch(0.18 0.01 260)",
                                  }}
                                />
                              ))}
                            </div>
                            {score > selfScore && (
                              <p className="text-[9px] text-destructive">▲ beats {shortName}</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    {c.key_products.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {c.key_products.slice(0, 4).map((p) => (
                          <Badge key={p} variant="secondary" className="text-[10px]">{p}</Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
}
