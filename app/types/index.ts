export interface Category {
  name: string;
  momentum_score: number;
  macro_adjustment: number;
  updated_at?: string;
}

export type TimeHorizon = "Short" | "Medium" | "Long";
export type ConfidenceTier = "High" | "Medium" | "Low";
export type Direction = "Bullish" | "Bearish" | "Neutral";
export type EntryType = "Breakout" | "Retest" | "Dip-Buy";
export type EntryQuality = "Strong" | "Moderate" | "Speculative";

export type TradeBias = "long" | "short" | "none";
export type BearishView = "spot" | "short";

export interface TradePlanLevels {
  ma20: number;
  ma50: number;
  swing_high: number;
  swing_low: number;
}

export interface TradePlan {
  bias: TradeBias;
  entry?: number;
  entry_condition?: string;
  target?: number;
  target_condition?: string;
  stop?: number;
  stop_condition?: string;
  risk_reward?: number | null;
  summary?: string;
  levels: TradePlanLevels;
}

export interface Candidate {
  symbol: string;
  name: string;
  category?: string;
  market_cap?: number;
  price: number;
  rsi: number;
  volume_ratio: number;
  technical_score: number;
  category_momentum: number;
  candidate_score: number;
  direction?: Direction;
  time_horizon?: TimeHorizon;
  confidence_tier?: ConfidenceTier;
  entry_type?: EntryType;
  entry_quality?: EntryQuality;
  rationale?: string;
  key_signals?: string[];
  trade_plan?: TradePlan;
  // Fundamental analysis (news/catalyst) — Agent 4
  fa_score?: number;        // sentiment × magnitude, [-1, 1]
  sentiment?: number;       // [-1, 1]
  catalyst?: string;        // short label, or "none"
  fa_summary?: string;
  fa_confidence?: ConfidenceTier;
  fa_sources?: FaSource[];
}

export interface FaSource {
  title?: string;
  url: string;
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

export type SortKey = "symbol" | "direction" | "horizon" | "confidence" | "score" | "market_cap";
export type SortOrder = "asc" | "desc" | null;

export interface FilterState {
  horizon?: TimeHorizon | "All";
  direction?: Direction | "All";
  confidence?: ConfidenceTier | "All";
}
