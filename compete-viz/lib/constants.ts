import type { CompetitorCategory, ThreatLevel, ProductCategory } from "./types";

export const CATEGORY_LABELS: Record<CompetitorCategory, string> = {
  tech_docs_service_info: "Tech Docs & Service Info",
  diagnostic_tools: "Diagnostic Tools",
  parts_catalogs: "Parts Catalogs",
  training_elearning: "Training & eLearning",
  content_mgmt_portals: "Content Mgmt & Portals",
};

export const CATEGORY_COLORS: Record<CompetitorCategory, string> = {
  tech_docs_service_info: "hsl(187 94% 42%)",
  diagnostic_tools: "hsl(262 83% 58%)",
  parts_catalogs: "hsl(142 71% 45%)",
  training_elearning: "hsl(25 95% 53%)",
  content_mgmt_portals: "hsl(330 80% 55%)",
};

export const CAPABILITY_LABELS: Record<ProductCategory, string> = {
  tech_docs: "Tech Docs",
  parts_catalogs: "Parts Catalogs",
  diagnostics: "Diagnostics",
  training: "Training",
  content_mgmt: "Content Mgmt",
};

export const THREAT_COLORS: Record<ThreatLevel, string> = {
  critical: "hsl(0 84% 60%)",
  high: "hsl(25 95% 53%)",
  moderate: "hsl(48 96% 53%)",
  low: "hsl(142 71% 45%)",
  minimal: "hsl(217 33% 40%)",
};

export const THREAT_LABELS: Record<ThreatLevel, string> = {
  critical: "Critical",
  high: "High",
  moderate: "Moderate",
  low: "Low",
  minimal: "Minimal",
};

export const HEATMAP_COLORS = [
  "hsl(217 33% 12%)",   // 0 — None
  "hsl(187 40% 18%)",   // 1 — Minimal
  "hsl(187 50% 25%)",   // 2 — Basic
  "hsl(187 60% 32%)",   // 3 — Moderate
  "hsl(187 75% 38%)",   // 4 — Strong
  "hsl(187 94% 42%)",   // 5 — Market-leading
];

export const SCORE_LABELS = [
  "None",
  "Minimal",
  "Basic",
  "Moderate",
  "Strong",
  "Market-Leading",
];

export const QUADRANT_LABELS = {
  topRight: "Leaders",
  topLeft: "Challengers",
  bottomLeft: "Niche Players",
  bottomRight: "Contenders",
};

export const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: "LayoutDashboard" },
  { href: "/matrix", label: "Feature Matrix", icon: "Grid3X3" },
  { href: "/quadrant", label: "Positioning", icon: "ScatterChart" },
  { href: "/categories", label: "Categories", icon: "Layers" },
  { href: "/threats", label: "Threats", icon: "ShieldAlert" },
  { href: "/gaps", label: "Gap Analysis", icon: "ArrowLeftRight" },
] as const;
