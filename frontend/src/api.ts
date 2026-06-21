import type { Property, SearchParams, SearchResponse, TrendPoint, EircodeResponse, AreaSummary, CountySummary } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

function buildUrl(path: string, params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const query = qs.toString();
  return `${BASE}${path}${query ? "?" + query : ""}`;
}

export async function searchProperties(params: SearchParams): Promise<SearchResponse> {
  const url = buildUrl("/search", {
    q:         params.q,
    radius_km: params.radius_km,
    min_year:  params.min_year,
    county:    params.county,
    limit:     params.limit,
  });

  try {
    console.log("[API] Fetching:", url);
    const res = await fetch(url);
    console.log("[API] Response status:", res.status, res.statusText);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error("[API] Error response:", err);

      if (res.status === 500) {
        throw new Error(`Server error (${res.status}). Please try again in a moment.`);
      } else if (res.status === 502 || res.status === 503 || res.status === 504) {
        throw new Error(`Service unavailable (${res.status}). Backend may be deploying.`);
      } else if (res.status === 404) {
        throw new Error("Could not find that address. Please check the spelling.");
      } else if (res.status === 429) {
        throw new Error("Too many requests. Please wait a moment and try again.");
      }
      throw new Error(err.detail ?? `Search failed: HTTP ${res.status}`);
    }
    return res.json();
  } catch (err) {
    console.error("[API] Fetch error:", err);
    if (err instanceof TypeError) {
      throw new Error(`Network error: ${err.message} - Backend URL: ${BASE}`);
    }
    throw err;
  }
}

export async function fetchTrends(
  q?: string,
  radius_km = 5,
  county?: string
): Promise<TrendPoint[]> {
  const url = buildUrl("/trends", { q, radius_km, county });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Trends failed (${res.status})`);
  const data = await res.json();
  return data.data;
}

export async function fetchEircode(
  code: string,
  opts: { min_price?: number; max_price?: number; min_year?: number; max_year?: number; limit?: number } = {}
): Promise<EircodeResponse> {
  const url = buildUrl("/eircode", { code, ...opts });
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Eircode lookup failed (${res.status})`);
  }
  return res.json();
}

export async function fetchAreaSummary(slug: string, name: string, radiusKm = 2): Promise<AreaSummary> {
  const [searchRes, trendsRes] = await Promise.all([
    fetch(buildUrl("/search", { q: name, radius_km: radiusKm, limit: 10 })),
    fetch(buildUrl("/trends", { q: name, radius_km: radiusKm })),
  ]);
  if (!searchRes.ok) {
    const err = await searchRes.json().catch(() => ({}));
    throw new Error(err.detail ?? `Area lookup failed (${searchRes.status})`);
  }
  const search = await searchRes.json();
  const trends = trendsRes.ok ? (await trendsRes.json()).data : [];

  const prices = search.results.map((r: any) => r.price as number);
  const allYears = trends.map((t: any) => t.year as number);

  return {
    name,
    slug,
    center: search.center,
    radius_km: radiusKm,
    total_count: search.count,
    median_price: trends.length ? trends[trends.length - 1].median_price : null,
    avg_price: prices.length ? Math.round(prices.reduce((a: number, b: number) => a + b, 0) / prices.length) : null,
    min_year: allYears.length ? Math.min(...allYears) : null,
    max_year: allYears.length ? Math.max(...allYears) : null,
    recent: search.results,
    trends,
  };
}

export async function fetchCountySummary(county: string): Promise<CountySummary> {
  const [countiesRes, trendsRes, searchRes] = await Promise.all([
    fetch(`${BASE}/counties`),
    fetch(buildUrl("/trends", { county })),
    fetch(buildUrl("/search", { q: `53.5,-7.5`, radius_km: 200, county, limit: 10 })),
  ]);
  const countiesData: { county: string; count: number }[] = await countiesRes.json();
  const trends = trendsRes.ok ? (await trendsRes.json()).data : [];
  const search = searchRes.ok ? await searchRes.json() : { results: [] };

  const countyRow = countiesData.find(r => r.county.toLowerCase() === county.toLowerCase());
  const latestTrend = trends[trends.length - 1];

  return {
    county,
    total_count: countyRow?.count ?? 0,
    median_price: latestTrend?.median_price ?? null,
    avg_price: latestTrend?.avg_price ?? null,
    trends,
    recent: search.results,
  };
}

export async function fetchNearestPins(params: SearchParams, limit = 10): Promise<Property[]> {
  // No date filter — always show the 10 physically closest sales regardless of period
  const url = buildUrl("/search", {
    q:         params.q,
    radius_km: params.radius_km,
    county:    params.county,
    sort:      "distance",
    limit,
  });
  const res = await fetch(url);
  if (!res.ok) return [];
  const data = await res.json();
  return data.results;
}

export async function fetchGeocode(q: string, county?: string): Promise<{ lat: number; lon: number }> {
  const url = buildUrl("/geocode", { q, county });
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Could not locate: ${q}`);
  }
  return res.json();
}

export async function submitFeedback(data: {
  datasets: string; comments: string; name: string; email: string;
}): Promise<void> {
  const res = await fetch(`${BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Could not send feedback");
}

export async function submitContact(data: {
  message: string; price_updates: boolean; name: string; email: string;
}): Promise<void> {
  const res = await fetch(`${BASE}/contact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Could not send message");
}

export async function fetchCounties(): Promise<string[]> {
  const res = await fetch(`${BASE}/counties`);
  if (!res.ok) throw new Error("Could not load counties");
  const data: { county: string }[] = await res.json();
  return data.map((r) => r.county);
}

export async function fetchNextPropertyToGeocode(): Promise<Property | null> {
  const res = await fetch(`${BASE}/geocoding-queue/next`);
  if (!res.ok) throw new Error("Could not fetch next property");
  const data = await res.json();
  return data.property;
}

export async function updatePropertyGeocode(
  propertyId: number,
  latitude: number,
  longitude: number,
  address?: string,
  eircode?: string
): Promise<void> {
  const body: any = { property_id: propertyId, latitude, longitude };
  if (address) body.address = address;
  if (eircode) body.eircode = eircode;

  const res = await fetch(`${BASE}/geocoding-queue/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Could not update geocode");
  }
}

export async function skipPropertyGeocode(propertyId: number): Promise<void> {
  const res = await fetch(`${BASE}/geocoding-queue/skip?property_id=${propertyId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Could not skip property");
}
