export type ProductCategory =
  | "tech_docs"
  | "parts_catalogs"
  | "diagnostics"
  | "training"
  | "content_mgmt";

export type MarketSegment =
  | "automotive_oem"
  | "automotive_aftermarket"
  | "heavy_equipment"
  | "powersports"
  | "aerospace_defense"
  | "ev_specialist"
  | "multi_industry";

export type CompetitorCategory =
  | "tech_docs_service_info"
  | "diagnostic_tools"
  | "parts_catalogs"
  | "training_elearning"
  | "content_mgmt_portals";

export type ThreatLevel = "critical" | "high" | "moderate" | "low" | "minimal";

export type CapabilityScore = 0 | 1 | 2 | 3 | 4 | 5;

export interface CapabilityProfile {
  tech_docs: CapabilityScore;
  parts_catalogs: CapabilityScore;
  diagnostics: CapabilityScore;
  training: CapabilityScore;
  content_mgmt: CapabilityScore;
}

export interface MarketPosition {
  capability: number;
  market_reach: number;
}

export interface Competitor {
  id: string;
  name: string;
  parent_company?: string;
  website: string;
  description: string;
  founded?: number;
  headquarters?: string;
  employees_approx?: string;
  revenue_approx?: string;
  category: CompetitorCategory;
  segments: MarketSegment[];
  threat_level: ThreatLevel;
  threat_score: number;
  capabilities: CapabilityProfile;
  position: MarketPosition;
  key_products: string[];
  strengths: string[];
  weaknesses: string[];
  our_advantages: string[];
  our_gaps: string[];
  notes?: string;
  last_updated: string;
  is_self?: boolean;
}

export interface CompetitiveDataset {
  metadata: {
    version: string;
    last_updated: string;
    compiled_by: string;
    total_competitors: number;
  };
  self: Competitor;
  competitors: Competitor[];
}

export interface HeatmapRow {
  id: string;
  name: string;
  category: CompetitorCategory;
  threat_level: ThreatLevel;
  scores: CapabilityProfile;
  is_self?: boolean;
}

export interface QuadrantPoint {
  id: string;
  name: string;
  x: number;
  y: number;
  category: CompetitorCategory;
  is_self?: boolean;
}
