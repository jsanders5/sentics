export interface Category {
  name: string;
  momentum_score: number;
  macro_adjustment: number;
  updated_at?: string;
}

export type TimeHorizon = "Short" | "Medium" | "Long";
export type ConfidenceTier = "High" | "Medium" | "Low";
export type EntryType = "Breakout" | "Retest" | "Dip-Buy";
export type EntryQuality = "Strong" | "Moderate" | "Speculative";

export interface Candidate {
  symbol: string;
  name: string;
  category: string;
  price: number;
  rsi: number;
  volume_ratio: number;
  technical_score: number;
  category_momentum: number;
  candidate_score: number;
  time_horizon?: TimeHorizon;
  confidence_tier?: ConfidenceTier;
  entry_type?: EntryType;
  entry_quality?: EntryQuality;
  rationale?: string;
  key_signals?: string[];
}

export interface PipelineRun {
  run_id: string;
  status: "success" | "error" | "partial";
  timestamp: string;
  categories: Category[];
  candidates: Candidate[];
  total_candidates: number;
  low_signal_environment?: boolean;
}

export type SortKey = "rank" | "symbol" | "category" | "horizon" | "confidence" | "score";
export type SortOrder = "asc" | "desc" | null;

export interface FilterState {
  horizon?: TimeHorizon | "All";
  category?: string | "All";
  confidence?: ConfidenceTier | "All";
}
