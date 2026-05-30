/**
 * County Data Cache System
 *
 * Caches county summary data in localStorage to reduce API calls.
 * Cache expires after 45 days.
 */

import type { CountySummary } from "../types";

const CACHE_KEY_PREFIX = "county_cache_";
const CACHE_DURATION_MS = 45 * 24 * 60 * 60 * 1000; // 45 days in milliseconds

interface CacheEntry {
  data: CountySummary;
  timestamp: number;
  version: number;  // For cache invalidation if data structure changes
}

const CACHE_VERSION = 1;

/**
 * Get cached county data if it exists and is not expired
 */
export function getCachedCountyData(county: string): CountySummary | null {
  try {
    const cacheKey = `${CACHE_KEY_PREFIX}${county.toLowerCase()}`;
    const cached = localStorage.getItem(cacheKey);

    if (!cached) {
      return null;
    }

    const entry: CacheEntry = JSON.parse(cached);

    // Check version
    if (entry.version !== CACHE_VERSION) {
      console.log(`[Cache] Invalidating ${county} - version mismatch`);
      localStorage.removeItem(cacheKey);
      return null;
    }

    // Check age
    const age = Date.now() - entry.timestamp;
    const ageInDays = Math.floor(age / (24 * 60 * 60 * 1000));

    if (age > CACHE_DURATION_MS) {
      console.log(`[Cache] Expired ${county} - ${ageInDays} days old`);
      localStorage.removeItem(cacheKey);
      return null;
    }

    console.log(`[Cache] Hit ${county} - ${ageInDays} days old`);
    return entry.data;
  } catch (error) {
    console.error(`[Cache] Error reading cache for ${county}:`, error);
    return null;
  }
}

/**
 * Save county data to cache
 */
export function setCachedCountyData(county: string, data: CountySummary): void {
  try {
    const cacheKey = `${CACHE_KEY_PREFIX}${county.toLowerCase()}`;
    const entry: CacheEntry = {
      data,
      timestamp: Date.now(),
      version: CACHE_VERSION,
    };

    localStorage.setItem(cacheKey, JSON.stringify(entry));
    console.log(`[Cache] Saved ${county}`);
  } catch (error) {
    // localStorage might be full or disabled
    console.error(`[Cache] Error saving cache for ${county}:`, error);
  }
}

/**
 * Clear cache for a specific county
 */
export function clearCountyCache(county: string): void {
  const cacheKey = `${CACHE_KEY_PREFIX}${county.toLowerCase()}`;
  localStorage.removeItem(cacheKey);
  console.log(`[Cache] Cleared ${county}`);
}

/**
 * Clear all county caches
 */
export function clearAllCountyCaches(): void {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(CACHE_KEY_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
    console.log("[Cache] Cleared all county caches");
  } catch (error) {
    console.error("[Cache] Error clearing all caches:", error);
  }
}

/**
 * Get cache info for debugging
 */
export function getCacheInfo(): Array<{
  county: string;
  ageInDays: number;
  size: number;
}> {
  const info: Array<{ county: string; ageInDays: number; size: number }> = [];

  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(CACHE_KEY_PREFIX)) {
        const county = key.replace(CACHE_KEY_PREFIX, "");
        const cached = localStorage.getItem(key);
        if (cached) {
          const entry: CacheEntry = JSON.parse(cached);
          const ageInDays = Math.floor((Date.now() - entry.timestamp) / (24 * 60 * 60 * 1000));
          const size = new Blob([cached]).size;
          info.push({ county, ageInDays, size });
        }
      }
    });
  } catch (error) {
    console.error("[Cache] Error getting cache info:", error);
  }

  return info;
}

/**
 * Check if localStorage is available and working
 */
export function isLocalStorageAvailable(): boolean {
  try {
    const test = "__localStorage_test__";
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Get total cache size in bytes
 */
export function getCacheSizeBytes(): number {
  let total = 0;
  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(CACHE_KEY_PREFIX)) {
        const item = localStorage.getItem(key);
        if (item) {
          total += new Blob([item]).size;
        }
      }
    });
  } catch (error) {
    console.error("[Cache] Error calculating cache size:", error);
  }
  return total;
}

/**
 * Format cache size for display
 */
export function formatCacheSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
