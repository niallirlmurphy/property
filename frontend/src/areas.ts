export interface AreaConfig {
  slug: string;
  name: string;
  query: string;  // what to pass to the search API
  radius_km: number;
  description: string;
  county: string;  // parent county slug (e.g. "dublin", "cork")
}

export const AREAS: AreaConfig[] = [
  { slug: "rathmines",      name: "Rathmines",       query: "Rathmines, Dublin",       radius_km: 1.5, description: "a popular inner-city suburb on Dublin's southside", county: "dublin" },
  { slug: "ranelagh",       name: "Ranelagh",         query: "Ranelagh, Dublin",        radius_km: 1,   description: "one of Dublin's most sought-after residential villages", county: "dublin" },
  { slug: "blackrock",      name: "Blackrock",        query: "Blackrock, Dublin",       radius_km: 1.5, description: "a coastal suburb south of Dublin city centre", county: "dublin" },
  { slug: "dun-laoghaire",  name: "Dún Laoghaire",   query: "Dún Laoghaire, Dublin",   radius_km: 2,   description: "a coastal town and harbour south of Dublin", county: "dublin" },
  { slug: "clontarf",       name: "Clontarf",         query: "Clontarf, Dublin",        radius_km: 1.5, description: "a seaside suburb on Dublin's northside", county: "dublin" },
  { slug: "howth",          name: "Howth",            query: "Howth, Dublin",           radius_km: 2,   description: "a picturesque fishing village and peninsula north of Dublin", county: "dublin" },
  { slug: "malahide",       name: "Malahide",         query: "Malahide, Dublin",        radius_km: 2,   description: "a coastal village north of Dublin known for its castle and marina", county: "dublin" },
  { slug: "stillorgan",     name: "Stillorgan",       query: "Stillorgan, Dublin",      radius_km: 1.5, description: "a suburban area in south County Dublin", county: "dublin" },
  { slug: "sandymount",     name: "Sandymount",       query: "Sandymount, Dublin",      radius_km: 1,   description: "a coastal village close to Dublin city centre", county: "dublin" },
  { slug: "portobello",     name: "Portobello",       query: "Portobello, Dublin",      radius_km: 1,   description: "a vibrant canalside neighbourhood in Dublin 8", county: "dublin" },
  { slug: "galway-city",    name: "Galway City",      query: "Galway City",             radius_km: 3,   description: "the cultural capital of the west of Ireland", county: "galway" },
  { slug: "salthill",       name: "Salthill",         query: "Salthill, Galway",        radius_km: 1.5, description: "a seaside suburb of Galway city with a popular promenade", county: "galway" },
  { slug: "oranmore",       name: "Oranmore",         query: "Oranmore, Galway",        radius_km: 2,   description: "a growing commuter town east of Galway city", county: "galway" },
  { slug: "athenry",        name: "Athenry",          query: "Athenry, Galway",         radius_km: 2,   description: "a historic walled town in County Galway", county: "galway" },
  { slug: "tuam",           name: "Tuam",             query: "Tuam, Galway",            radius_km: 2,   description: "a market town in north County Galway", county: "galway" },
  { slug: "connemara",      name: "Connemara",        query: "Clifden, Galway",         radius_km: 5,   description: "a scenic rural region on Galway's western coast", county: "galway" },
  { slug: "cork-city",      name: "Cork City",        query: "Cork City",               radius_km: 3,   description: "Ireland's second city on the River Lee", county: "cork" },
  { slug: "douglas",        name: "Douglas",          query: "Douglas, Cork",           radius_km: 1.5, description: "an upscale suburb on Cork city's southside", county: "cork" },
  { slug: "ballincollig",   name: "Ballincollig",     query: "Ballincollig, Cork",      radius_km: 2,   description: "a large commuter town west of Cork city", county: "cork" },
  { slug: "carrigaline",    name: "Carrigaline",      query: "Carrigaline, Cork",       radius_km: 2,   description: "a growing town south of Cork city", county: "cork" },
  { slug: "cobh",           name: "Cobh",             query: "Cobh, Cork",              radius_km: 2,   description: "a historic port town on Cork harbour", county: "cork" },
  { slug: "midleton",       name: "Midleton",         query: "Midleton, Cork",          radius_km: 2,   description: "a market town and distillery gateway in East Cork", county: "cork" },
  { slug: "kinsale",        name: "Kinsale",          query: "Kinsale, Cork",           radius_km: 2,   description: "a coastal gourmet destination and sailing hub in County Cork", county: "cork" },
  { slug: "limerick-city",  name: "Limerick City",    query: "Limerick City",           radius_km: 3,   description: "a vibrant city on the River Shannon", county: "limerick" },
  { slug: "waterford-city", name: "Waterford City",   query: "Waterford City",          radius_km: 3,   description: "Ireland's oldest city on the River Suir", county: "waterford" },
  { slug: "kilkenny-city",  name: "Kilkenny City",    query: "Kilkenny",                radius_km: 2,   description: "the medieval capital of Ireland", county: "kilkenny" },
  { slug: "drogheda",       name: "Drogheda",         query: "Drogheda, Louth",         radius_km: 2,   description: "a major town on the River Boyne in County Louth", county: "louth" },
  { slug: "dundalk",        name: "Dundalk",          query: "Dundalk, Louth",          radius_km: 2,   description: "the largest town in County Louth", county: "louth" },
  { slug: "navan",          name: "Navan",            query: "Navan, Meath",            radius_km: 2,   description: "the county town of Meath", county: "meath" },
  { slug: "naas",           name: "Naas",             query: "Naas, Kildare",           radius_km: 2,   description: "the county town of Kildare", county: "kildare" },
  { slug: "bray",           name: "Bray",             query: "Bray, Wicklow",           radius_km: 2,   description: "a seaside town at the foot of the Wicklow Mountains", county: "wicklow" },
];

export const COUNTIES = [
  "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway",
  "Kerry","Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford",
  "Louth","Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo",
  "Tipperary","Waterford","Westmeath","Wexford","Wicklow",
];

export function countySlug(county: string): string {
  return county.toLowerCase().replace(/\s+/g, "-");
}

export function countyFromSlug(slug: string): string | undefined {
  return COUNTIES.find(c => countySlug(c) === slug);
}

export function areaFromSlug(slug: string): AreaConfig | undefined {
  return AREAS.find(a => a.slug === slug);
}

// Dublin eircode routing keys with friendly names
export const DUBLIN_EIRCODE_AREAS: Record<string, string> = {
  D01: "Dublin 1", D02: "Dublin 2", D03: "Dublin 3", D04: "Dublin 4",
  D05: "Dublin 5", D06: "Dublin 6", D6W: "Dublin 6W", D07: "Dublin 7",
  D08: "Dublin 8", D09: "Dublin 9", D10: "Dublin 10", D11: "Dublin 11",
  D12: "Dublin 12", D13: "Dublin 13", D14: "Dublin 14", D15: "Dublin 15",
  D16: "Dublin 16", D17: "Dublin 17", D18: "Dublin 18", D20: "Dublin 20",
  D22: "Dublin 22", D24: "Dublin 24",
};

// Provinces of the Republic of Ireland → county slugs (display order).
// Covers all 26 counties in COUNTIES.
export const PROVINCES: { name: string; counties: string[] }[] = [
  { name: "Leinster", counties: ["carlow", "dublin", "kildare", "kilkenny", "laois", "longford", "louth", "meath", "offaly", "westmeath", "wexford", "wicklow"] },
  { name: "Munster",  counties: ["clare", "cork", "kerry", "limerick", "tipperary", "waterford"] },
  { name: "Connacht", counties: ["galway", "leitrim", "mayo", "roscommon", "sligo"] },
  { name: "Ulster",   counties: ["cavan", "donegal", "monaghan"] },
];

// All AREAS whose parent county matches the given county slug.
export function areasForCounty(countySlug: string): AreaConfig[] {
  return AREAS.filter(a => a.county === countySlug);
}

// The province name a county slug belongs to (undefined if unknown).
export function provinceForCounty(countySlug: string): string | undefined {
  return PROVINCES.find(p => p.counties.includes(countySlug))?.name;
}

// The parent county slug for an area slug (undefined if unknown).
export function countyForArea(areaSlug: string): string | undefined {
  return AREAS.find(a => a.slug === areaSlug)?.county;
}
