"use client";

import { useState } from "react";
import { getQuadrantData } from "@/lib/data";
import { CATEGORY_LABELS, CATEGORY_COLORS } from "@/lib/constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";
import type { CompetitorCategory } from "@/lib/types";

function CustomDot(props: { cx?: number; cy?: number; payload?: { is_tweddle?: boolean; category: CompetitorCategory } }) {
  const { cx = 0, cy = 0, payload } = props;
  if (payload?.is_tweddle) {
    return (
      <g>
        <circle cx={cx} cy={cy} r={10} fill="oklch(0.795 0.184 86)" stroke="oklch(0.795 0.184 86)" strokeWidth={2} opacity={0.3} />
        <circle cx={cx} cy={cy} r={6} fill="oklch(0.795 0.184 86)" stroke="oklch(0.9 0.1 86)" strokeWidth={2} />
      </g>
    );
  }
  const color = payload?.category ? CATEGORY_COLORS[payload.category] : "oklch(0.6 0.01 260)";
  return <circle cx={cx} cy={cy} r={5} fill={color} stroke={color} strokeWidth={1} opacity={0.8} />;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { name: string; x: number; y: number; category: CompetitorCategory; is_tweddle?: boolean } }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-lg">
      <p className={`text-sm font-bold ${d.is_tweddle ? "text-accent" : ""}`}>{d.name}</p>
      <p className="text-xs text-muted-foreground">{CATEGORY_LABELS[d.category]}</p>
      <div className="mt-1 grid grid-cols-2 gap-x-4 text-xs">
        <span className="text-muted-foreground">Capability:</span>
        <span className="font-mono">{d.y}</span>
        <span className="text-muted-foreground">Market Reach:</span>
        <span className="font-mono">{d.x}</span>
      </div>
    </div>
  );
}

export default function QuadrantPage() {
  const allData = getQuadrantData();
  const [visibleCategories, setVisibleCategories] = useState<Set<CompetitorCategory>>(
    new Set(Object.keys(CATEGORY_LABELS) as CompetitorCategory[])
  );

  const filtered = allData.filter(
    (d) => d.is_tweddle || visibleCategories.has(d.category)
  );

  const toggleCategory = (cat: CompetitorCategory) => {
    setVisibleCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Market Positioning</h1>
        <p className="text-sm text-muted-foreground">
          Capability vs Market Reach — {filtered.length} competitors plotted
        </p>
      </div>

      <div className="flex items-center gap-2">
        {(Object.keys(CATEGORY_LABELS) as CompetitorCategory[]).map((cat) => (
          <button
            key={cat}
            onClick={() => toggleCategory(cat)}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition-all ${
              visibleCategories.has(cat) ? "bg-secondary" : "bg-secondary/30 opacity-40"
            }`}
          >
            <div className="h-2 w-2 rounded-full" style={{ background: CATEGORY_COLORS[cat] }} />
            {CATEGORY_LABELS[cat]}
          </button>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          <ResponsiveContainer width="100%" height={550}>
            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
              <CartesianGrid stroke="oklch(0.2 0.01 260)" strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="x"
                domain={[0, 100]}
                name="Market Reach"
                tick={{ fill: "oklch(0.5 0.01 260)", fontSize: 11 }}
                label={{ value: "Market Reach →", position: "bottom", fill: "oklch(0.5 0.01 260)", fontSize: 12 }}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={[0, 100]}
                name="Capability"
                tick={{ fill: "oklch(0.5 0.01 260)", fontSize: 11 }}
                label={{ value: "Capability →", angle: -90, position: "left", fill: "oklch(0.5 0.01 260)", fontSize: 12 }}
              />
              <ReferenceLine x={50} stroke="oklch(0.3 0.01 260)" strokeDasharray="8 8" />
              <ReferenceLine y={50} stroke="oklch(0.3 0.01 260)" strokeDasharray="8 8" />
              <Tooltip content={<CustomTooltip />} />
              <Scatter data={filtered} shape={<CustomDot />}>
                {filtered.map((entry) => (
                  <Cell key={entry.id} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          {/* Quadrant labels */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="text-right text-xs text-muted-foreground/50">Challengers (high capability, low reach)</div>
            <div className="text-left text-xs text-muted-foreground/50">Leaders (high capability, high reach)</div>
            <div className="text-right text-xs text-muted-foreground/50">Niche Players (low capability, low reach)</div>
            <div className="text-left text-xs text-muted-foreground/50">Contenders (low capability, high reach)</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
