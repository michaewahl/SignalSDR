import dataset from "@/data/competitors.json";
import type {
  Competitor,
  CompetitiveDataset,
  CompetitorCategory,
  HeatmapRow,
  ProductCategory,
  QuadrantPoint,
  ThreatLevel,
} from "./types";

const data = dataset as CompetitiveDataset;

export function getSelf(): Competitor {
  return data.self;
}

export function getCompetitors(): Competitor[] {
  return data.competitors;
}

export function getAllEntries(): Competitor[] {
  return [data.self, ...data.competitors];
}

export function getCompetitorById(id: string): Competitor | undefined {
  if (id === data.self.id) return data.self;
  return data.competitors.find((c) => c.id === id);
}

export function getMetadata() {
  return data.metadata;
}

// Derived data for views

export function getByCategory(cat: CompetitorCategory): Competitor[] {
  return data.competitors.filter((c) => c.category === cat);
}

export function getByThreatLevel(level: ThreatLevel): Competitor[] {
  return data.competitors.filter((c) => c.threat_level === level);
}

export function getTopThreats(n: number = 5): Competitor[] {
  return [...data.competitors]
    .sort((a, b) => b.threat_score - a.threat_score)
    .slice(0, n);
}

export function getCategoryCounts(): Record<CompetitorCategory, number> {
  const counts = {} as Record<CompetitorCategory, number>;
  for (const c of data.competitors) {
    counts[c.category] = (counts[c.category] || 0) + 1;
  }
  return counts;
}

export function getThreatCounts(): Record<ThreatLevel, number> {
  const counts = {} as Record<ThreatLevel, number>;
  for (const c of data.competitors) {
    counts[c.threat_level] = (counts[c.threat_level] || 0) + 1;
  }
  return counts;
}

export function getAverageCapabilities(): Record<ProductCategory, number> {
  const sums = { tech_docs: 0, parts_catalogs: 0, diagnostics: 0, training: 0, content_mgmt: 0 };
  const n = data.competitors.length;
  for (const c of data.competitors) {
    for (const key of Object.keys(sums) as ProductCategory[]) {
      sums[key] += c.capabilities[key];
    }
  }
  return Object.fromEntries(
    Object.entries(sums).map(([k, v]) => [k, Math.round((v / n) * 10) / 10])
  ) as Record<ProductCategory, number>;
}

export function getSelfRank(): number {
  const all = getAllEntries();
  const sorted = [...all].sort((a, b) => {
    const aTotal = Object.values(a.capabilities).reduce((s, v) => s + v, 0);
    const bTotal = Object.values(b.capabilities).reduce((s, v) => s + v, 0);
    return bTotal - aTotal;
  });
  return sorted.findIndex((c) => c.is_self) + 1;
}

export function getHeatmapData(): HeatmapRow[] {
  return getAllEntries().map((c) => ({
    id: c.id,
    name: c.name,
    category: c.category,
    threat_level: c.threat_level,
    scores: c.capabilities,
    is_self: c.is_self,
  }));
}

export function getQuadrantData(): QuadrantPoint[] {
  return getAllEntries().map((c) => ({
    id: c.id,
    name: c.name,
    x: c.position.market_reach,
    y: c.position.capability,
    category: c.category,
    is_self: c.is_self,
  }));
}
