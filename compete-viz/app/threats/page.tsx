"use client";

import Link from "next/link";
import { getCompetitors } from "@/lib/data";
import { CATEGORY_LABELS, CATEGORY_COLORS, THREAT_COLORS, THREAT_LABELS } from "@/lib/constants";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import type { ThreatLevel } from "@/lib/types";

export default function ThreatsPage() {
  const competitors = [...getCompetitors()].sort((a, b) => b.threat_score - a.threat_score);

  const allTiers: { level: ThreatLevel; items: typeof competitors }[] = [
    { level: "critical" as ThreatLevel, items: competitors.filter((c) => c.threat_level === "critical") },
    { level: "high" as ThreatLevel, items: competitors.filter((c) => c.threat_level === "high") },
    { level: "moderate" as ThreatLevel, items: competitors.filter((c) => c.threat_level === "moderate") },
    { level: "low" as ThreatLevel, items: competitors.filter((c) => c.threat_level === "low") },
    { level: "minimal" as ThreatLevel, items: competitors.filter((c) => c.threat_level === "minimal") },
  ];
  const tiers = allTiers.filter((t) => t.items.length > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Threat Ranking</h1>
        <p className="text-sm text-muted-foreground">
          {competitors.length} competitors ranked by threat score (0-100)
        </p>
      </div>

      {tiers.map((tier, tierIdx) => (
        <div key={tier.level} className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full" style={{ background: THREAT_COLORS[tier.level] }} />
            <h2 className="text-sm font-bold uppercase tracking-wider" style={{ color: THREAT_COLORS[tier.level] }}>
              {THREAT_LABELS[tier.level]} ({tier.items.length})
            </h2>
          </div>

          {tier.items.map((c, i) => {
            const rank = competitors.indexOf(c) + 1;
            return (
              <Card key={c.id} className={tier.level === "critical" ? "border-destructive/30" : ""}>
                <CardContent className="pt-4">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-secondary font-mono text-sm font-bold text-muted-foreground">
                      #{rank}
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Link href={`/competitor/${c.id}`} className="font-bold hover:text-primary transition-colors">
                            {c.name}
                          </Link>
                          {c.parent_company && (
                            <span className="text-xs text-muted-foreground">({c.parent_company})</span>
                          )}
                          <Badge variant="secondary" className="text-[10px]" style={{ color: CATEGORY_COLORS[c.category] }}>
                            {CATEGORY_LABELS[c.category]}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Progress value={c.threat_score} className="h-2 w-24" />
                          <span className="font-mono text-sm font-bold" style={{ color: THREAT_COLORS[c.threat_level] }}>
                            {c.threat_score}
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">{c.description}</p>
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <p className="font-medium text-chart-3 mb-1">Our Advantages</p>
                          <ul className="space-y-0.5 text-muted-foreground">
                            {c.our_advantages.map((a, i) => (
                              <li key={i}>+ {a}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-destructive mb-1">Our Gaps</p>
                          <ul className="space-y-0.5 text-muted-foreground">
                            {c.our_gaps.map((g, i) => (
                              <li key={i}>- {g}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {tierIdx < tiers.length - 1 && <Separator className="my-4" />}
        </div>
      ))}
    </div>
  );
}
