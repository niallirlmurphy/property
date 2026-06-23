export interface Property {
  id: number;
  sale_date: string;
  address: string;
  county: string | null;
  eircode: string | null;
  price: number;
  not_full_market_price: boolean;
  vat_exclusive: boolean;
  description: string | null;
  size_description: string | null;
  latitude: number | null;
  longitude: number | null;
  bedrooms: number | null;
  property_type: string | null;
  distance_m?: number;
}

export interface SearchResponse {
  center: { lat: number; lon: number };
  radius_km: number;
  count: number;
  results: Property[];
}

export interface TrendPoint {
  year: number;
  count: number;
  median_price: number;
  avg_price: number;
  min_price: number;
  max_price: number;
}

export interface SearchParams {
  q: string;
  radius_km: number;
  min_year?: number;
  county?: string;
  limit?: number;
}

export interface AreaSummary {
  name: string;
  slug: string;
  center: { lat: number; lon: number };
  radius_km: number;
  total_count: number;
  median_price: number | null;
  avg_price: number | null;
  min_year: number | null;
  max_year: number | null;
  recent: Property[];
  trends: TrendPoint[];
}

export interface CountySummary {
  county: string;
  total_count: number;
  median_price: number | null;
  avg_price: number | null;
  trends: TrendPoint[];
  recent: Property[];
}

export interface EircodeStats {
  total_count: number;
  median_price: number | null;
  avg_price: number | null;
  earliest_sale: string | null;
  latest_sale: string | null;
}

export interface EircodeResponse {
  code: string;
  match_type: "full_eircode" | "routing_key";
  stats: EircodeStats;
  count: number;
  results: Omit<Property, "distance_m">[];
}

// Valuation types
export interface ValuationRequest {
  address: string;
  eircode?: string;
  valuation_date?: string;
}

export interface ComparableProperty {
  id: number;
  address: string;
  price: number;
  adjusted_price: number;
  sale_date: string;
  distance_m: number;
  weight: number;
  bedrooms?: number | null;
  property_type?: string | null;
  temporal_adjustment_factor?: number;
  recency_score?: number;
}

export interface ConfidenceInterval {
  lower: number;
  upper: number;
  width_pct: number;
}

export interface ValidationWarning {
  level: "info" | "warning" | "error";
  message: string;
  code?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  confidence_level: "high" | "medium" | "low";
  quality_score: number;
  warnings: ValidationWarning[];
  n_comparables: number;
  avg_distance_km: number;
  price_dispersion_cv?: number;
}

export interface ValuationStatistics {
  mean_price: number;
  median_price: number;
  std_dev: number;
  coefficient_of_variation: number;
  min_price: number;
  max_price: number;
}

export interface ValuationResponse {
  estimate: number;
  confidence_interval: ConfidenceInterval;
  validation: ValidationResult;
  comparables: ComparableProperty[];
  statistics: ValuationStatistics;
  metadata: {
    geocoded_location: {
      latitude: number;
      longitude: number;
      confidence: number;
      method: string;
      address_matched?: string;
    };
    valuation_date: string;
    algorithm_version: string;
    processing_time_ms: number;
  };
}
