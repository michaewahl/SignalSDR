"use client";

import { getCompetitors, getSelf, getAverageCapabilities } from "@/lib/data";
import { getShortName } from "@/lib/company";
import { CAPABILITY_LABELS, HEATMAP_COLORS } from "@/lib/constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Legend,
} from "recharts";
import type { ProductCategory } from "@/lib/types";

export default function GapsPage() {
  const self = getSelf();
  const shortName = getShortName();
  const competitors = getCompetitors();
  const avgCaps = getAverageCapabilities();
  const dimensions = Object.keys(CAPABILITY_LABELS) as ProductCategory[];

  const barData = dimensions.map((dim) => ({
    dimension: CAPABILITY_LABELS[dim],
    [shortName]: self.capabilities[dim],
    "Industry Avg": avgCaps[dim],
    "Best Competitor": Math.max(...competitors.map((c) => c.capabilities[dim])),
  }));

  const advantages = dimensions.filter((dim) => self.capabilities[dim] > avgCaps[dim]);
  const gaps = dimensions.filter((dim) => self.capabilities[dim] <= avgCaps[dim]);

  const gapDetails = dimensions.map((dim) => {
    const beaters = competitors
      .filter((c) => c.capabilities[dim] > self.capabilities[dim])
      .sort((a, b) => b.capabilities[dim] - a.capabilities[dim]);
    return { dim, beaters };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Gap Analysis</h1>
        <p className="text-sm text-muted-foreground">
          {shortName}&apos;s capabilities vs industry average and best-in-class competitors
        </p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Capability Comparison</CardTitle></CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={barData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.2 0.01 260)" />
              <XAxis dataKey="dimension" tick={{ fill: "oklch(0.6 0.01 260)", fontSize: 11 }} />
              <YAxis domain={[0, 5]} tick={{ fill: "oklch(0.6 0.01 260)", fontSize: 11 }} ticks={[0, 1, 2, 3, 4, 5]} />
              <Tooltip contentStyle={{ background: "oklch(0.16 0.015 260)", border: "1px solid oklch(0.25 0.015 260)", borderRadius: "6px" }} itemStyle={{ color: "oklch(0.93 0.005 260)" }} />
              <Legend wrapperStyle={{ fontSize: 11, color: "oklch(0.6 0.01 260)" }} />
              <Bar dataKey={shortName} fill="oklch(0.795 0.184 86)" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Industry Avg" fill="oklch(0.4 0.01 260)" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Best Competitor" fill="oklch(0.715 0.143 211)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-chart-3">Our Advantages ({advantages.length})</h2>
          {advantages.map((dim) => {
            const diff = self.capabilities[dim] - avgCaps[dim];
            return (
              <Card key={dim} className="border-chart-3/20">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold">{CAPABILITY_LABELS[dim]}</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">Score</span>
                      <span className="text-sm font-mono font-bold" style={{ color: HEATMAP_COLORS[self.capabilities[dim]] }}>{self.capabilities[dim]}/5</span>
                    </div>
                  </div>
                  <p className="text-xs text-chart-3 mt-1">+{diff.toFixed(1)} above industry average ({avgCaps[dim].toFixed(1)})</p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="space-y-3">
          <h2 className="text-sm font-bold text-destructive">Competitor Leads ({gaps.length})</h2>
          {gaps.length === 0 ? (
            <Card><CardContent className="pt-4"><p className="text-sm text-muted-foreground">{shortName} scores above industry average in all dimensions.</p></CardContent></Card>
          ) : (
            gaps.map((dim) => {
              const diff = avgCaps[dim] - self.capabilities[dim];
              const detail = gapDetails.find((d) => d.dim === dim);
              return (
                <Card key={dim} className="border-destructive/20">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold">{CAPABILITY_LABELS[dim]}</h3>
                      <span className="text-sm font-mono font-bold text-destructive">{self.capabilities[dim]}/5</span>
                    </div>
                    <p className="text-xs text-destructive mt-1">-{diff.toFixed(1)} below industry average ({avgCaps[dim].toFixed(1)})</p>
                    {detail && detail.beaters.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        <span className="text-[10px] text-muted-foreground">Beaten by:</span>
                        {detail.beaters.slice(0, 5).map((c) => (
                          <Badge key={c.id} variant="outline" className="text-[10px]">{c.name} ({c.capabilities[dim]})</Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Who Beats {shortName} (Per Dimension)</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {gapDetails.map(({ dim, beaters }) => (
              <div key={dim}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium">{CAPABILITY_LABELS[dim]}</span>
                  <span className="text-xs text-muted-foreground">{shortName}: {self.capabilities[dim]}/5 &middot; {beaters.length} competitors ahead</span>
                </div>
                {beaters.length === 0 ? (
                  <p className="text-xs text-chart-3">No competitor scores higher than {shortName}</p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {beaters.map((c) => (
                      <Badge key={c.id} variant="secondary" className="text-[10px]">{c.name} ({c.capabilities[dim]})</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
