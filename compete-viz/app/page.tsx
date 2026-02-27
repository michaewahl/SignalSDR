"use client";

import {
  getCompetitors,
  getTweddle,
  getTopThreats,
  getCategoryCounts,
  getThreatCounts,
  getAverageCapabilities,
  getTweddleRank,
  getMetadata,
} from "@/lib/data";
import { CATEGORY_LABELS, CATEGORY_COLORS, THREAT_COLORS, CAPABILITY_LABELS } from "@/lib/constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { CompetitorCategory, ProductCategory } from "@/lib/types";
import { ShieldAlert, Target, Trophy, Zap } from "lucide-react";
import Link from "next/link";

export default function OverviewPage() {
  const competitors = getCompetitors();
  const tweddle = getTweddle();
  const topThreats = getTopThreats(5);
  const categoryCounts = getCategoryCounts();
  const threatCounts = getThreatCounts();
  const avgCaps = getAverageCapabilities();
  const tweddleRank = getTweddleRank();
  const meta = getMetadata();

  const criticalHighCount =
    (threatCounts.critical || 0) + (threatCounts.high || 0);

  const tweddleBestDim = (Object.entries(tweddle.capabilities) as [ProductCategory, number][])
    .sort((a, b) => b[1] - a[1])[0];

  const pieData = (Object.entries(categoryCounts) as [CompetitorCategory, number][]).map(
    ([cat, count]) => ({
      name: CATEGORY_LABELS[cat],
      value: count,
      color: CATEGORY_COLORS[cat],
    })
  );

  const radarData = (Object.keys(CAPABILITY_LABELS) as ProductCategory[]).map((key) => ({
    dimension: CAPABILITY_LABELS[key],
    Tweddle: tweddle.capabilities[key],
    "Top Competitor": Math.max(...topThreats.map((t) => t.capabilities[key])),
    Average: avgCaps[key],
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tweddle Group Competitive Intelligence</h1>
        <p className="text-sm text-muted-foreground">
          Tracking {meta.total_competitors} competitors across 5 product categories
          &middot; Last updated {meta.last_updated}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-primary/10 p-2">
                <Target className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{competitors.length}</p>
                <p className="text-xs text-muted-foreground">Competitors Tracked</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-destructive/10 p-2">
                <ShieldAlert className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <p className="text-2xl font-bold">{criticalHighCount}</p>
                <p className="text-xs text-muted-foreground">Critical / High Threats</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-accent/10 p-2">
                <Trophy className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="text-2xl font-bold">#{tweddleRank}</p>
                <p className="text-xs text-muted-foreground">Overall Capability Rank</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-primary/10 p-2">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{CAPABILITY_LABELS[tweddleBestDim[0]]}</p>
                <p className="text-xs text-muted-foreground">Strongest Dimension ({tweddleBestDim[1]}/5)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Segment Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Competitor Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center">
              <ResponsiveContainer width={200} height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "oklch(0.16 0.015 260)", border: "1px solid oklch(0.25 0.015 260)", borderRadius: "6px" }}
                    itemStyle={{ color: "oklch(0.93 0.005 260)" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 space-y-1.5">
              {pieData.map((entry) => (
                <div key={entry.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="h-2.5 w-2.5 rounded-full" style={{ background: entry.color }} />
                    <span className="text-muted-foreground">{entry.name}</span>
                  </div>
                  <span className="font-medium">{entry.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Capability Radar */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Tweddle vs Competition</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="oklch(0.25 0.015 260)" />
                <PolarAngleAxis
                  dataKey="dimension"
                  tick={{ fill: "oklch(0.6 0.01 260)", fontSize: 11 }}
                />
                <Radar
                  name="Tweddle"
                  dataKey="Tweddle"
                  stroke="oklch(0.795 0.184 86)"
                  fill="oklch(0.795 0.184 86)"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
                <Radar
                  name="Top Competitor"
                  dataKey="Top Competitor"
                  stroke="oklch(0.715 0.143 211)"
                  fill="oklch(0.715 0.143 211)"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Radar
                  name="Average"
                  dataKey="Average"
                  stroke="oklch(0.4 0.01 260)"
                  fill="none"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                />
                <Tooltip
                  contentStyle={{ background: "oklch(0.16 0.015 260)", border: "1px solid oklch(0.25 0.015 260)", borderRadius: "6px" }}
                  itemStyle={{ color: "oklch(0.93 0.005 260)" }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Threats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Top Threats</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topThreats.map((c, i) => (
              <div key={c.id} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground font-mono">#{i + 1}</span>
                    <Link href={`/competitor/${c.id}`} className="text-sm font-medium truncate hover:text-primary transition-colors">
                      {c.name}
                    </Link>
                  </div>
                  <Badge
                    variant="outline"
                    className="text-[10px] px-1.5 py-0"
                    style={{ borderColor: THREAT_COLORS[c.threat_level], color: THREAT_COLORS[c.threat_level] }}
                  >
                    {c.threat_level}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Progress value={c.threat_score} className="h-1.5" />
                  <span className="text-xs text-muted-foreground font-mono w-7">{c.threat_score}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
