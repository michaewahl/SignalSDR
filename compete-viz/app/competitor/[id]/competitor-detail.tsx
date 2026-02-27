"use client";

import { getCompetitorById, getSelf } from "@/lib/data";
import { getShortName } from "@/lib/company";
import { CATEGORY_LABELS, CATEGORY_COLORS, THREAT_COLORS, CAPABILITY_LABELS } from "@/lib/constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, Legend,
} from "recharts";
import type { ProductCategory } from "@/lib/types";
import { ArrowLeft, ExternalLink } from "lucide-react";
import Link from "next/link";

export default function CompetitorDetail({ id }: { id: string }) {
  const competitor = getCompetitorById(id);
  const self = getSelf();
  const shortName = getShortName();

  if (!competitor) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Competitor not found</p>
      </div>
    );
  }

  const radarData = (Object.keys(CAPABILITY_LABELS) as ProductCategory[]).map((key) => ({
    dimension: CAPABILITY_LABELS[key],
    [competitor.name]: competitor.capabilities[key],
    [shortName]: self.capabilities[key],
  }));

  return (
    <div className="space-y-6 max-w-4xl">
      <Link href="/threats" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-3 w-3" />
        Back to Threats
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className={`text-2xl font-bold ${competitor.is_self ? "text-accent" : ""}`}>{competitor.name}</h1>
            {competitor.parent_company && <span className="text-sm text-muted-foreground">({competitor.parent_company})</span>}
          </div>
          <p className="text-sm text-muted-foreground mt-1">{competitor.description}</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge style={{ background: CATEGORY_COLORS[competitor.category], color: "white" }} className="text-[10px]">{CATEGORY_LABELS[competitor.category]}</Badge>
            {!competitor.is_self && (
              <Badge variant="outline" style={{ borderColor: THREAT_COLORS[competitor.threat_level], color: THREAT_COLORS[competitor.threat_level] }}>
                Threat: {competitor.threat_level} ({competitor.threat_score}/100)
              </Badge>
            )}
            <a href={competitor.website} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
              {competitor.website} <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 text-xs">
        {competitor.founded && <Card><CardContent className="pt-3 pb-3"><p className="text-muted-foreground">Founded</p><p className="font-bold">{competitor.founded}</p></CardContent></Card>}
        {competitor.headquarters && <Card><CardContent className="pt-3 pb-3"><p className="text-muted-foreground">HQ</p><p className="font-bold">{competitor.headquarters}</p></CardContent></Card>}
        {competitor.employees_approx && <Card><CardContent className="pt-3 pb-3"><p className="text-muted-foreground">Employees</p><p className="font-bold">{competitor.employees_approx}</p></CardContent></Card>}
        {competitor.revenue_approx && <Card><CardContent className="pt-3 pb-3"><p className="text-muted-foreground">Revenue</p><p className="font-bold">{competitor.revenue_approx}</p></CardContent></Card>}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-sm">Capability Comparison</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="oklch(0.25 0.015 260)" />
                <PolarAngleAxis dataKey="dimension" tick={{ fill: "oklch(0.6 0.01 260)", fontSize: 11 }} />
                <Radar name={shortName} dataKey={shortName} stroke="oklch(0.795 0.184 86)" fill="oklch(0.795 0.184 86)" fillOpacity={0.2} strokeWidth={2} />
                <Radar name={competitor.name} dataKey={competitor.name} stroke="oklch(0.715 0.143 211)" fill="oklch(0.715 0.143 211)" fillOpacity={0.15} strokeWidth={2} />
                <Tooltip contentStyle={{ background: "oklch(0.16 0.015 260)", border: "1px solid oklch(0.25 0.015 260)", borderRadius: "6px" }} itemStyle={{ color: "oklch(0.93 0.005 260)" }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">Key Products</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {competitor.key_products.map((p) => (
              <div key={p} className="flex items-center gap-2 text-sm"><div className="h-1.5 w-1.5 rounded-full bg-primary" />{p}</div>
            ))}
            <Separator className="my-3" />
            <div className="space-y-1.5">
              <p className="text-xs font-medium">Market Segments</p>
              <div className="flex flex-wrap gap-1">
                {competitor.segments.map((s) => <Badge key={s} variant="secondary" className="text-[10px]">{s.replace(/_/g, " ")}</Badge>)}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {!competitor.is_self && (
        <div className="grid grid-cols-2 gap-6">
          <Card className="border-chart-3/20">
            <CardHeader><CardTitle className="text-sm text-chart-3">Our Advantages</CardTitle></CardHeader>
            <CardContent>
              <ul className="space-y-1.5 text-sm">
                {competitor.our_advantages.map((a, i) => (
                  <li key={i} className="flex items-start gap-2"><span className="text-chart-3 mt-0.5">+</span><span className="text-muted-foreground">{a}</span></li>
                ))}
              </ul>
            </CardContent>
          </Card>
          <Card className="border-destructive/20">
            <CardHeader><CardTitle className="text-sm text-destructive">Our Gaps</CardTitle></CardHeader>
            <CardContent>
              <ul className="space-y-1.5 text-sm">
                {competitor.our_gaps.map((g, i) => (
                  <li key={i} className="flex items-start gap-2"><span className="text-destructive mt-0.5">-</span><span className="text-muted-foreground">{g}</span></li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-sm">Strengths</CardTitle></CardHeader>
          <CardContent><ul className="space-y-1 text-sm text-muted-foreground">{competitor.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Weaknesses</CardTitle></CardHeader>
          <CardContent><ul className="space-y-1 text-sm text-muted-foreground">{competitor.weaknesses.map((w, i) => <li key={i}>{w}</li>)}</ul></CardContent>
        </Card>
      </div>
    </div>
  );
}
