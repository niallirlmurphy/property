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
