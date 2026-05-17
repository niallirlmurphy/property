export interface AreaConfig {
  slug: string;
  name: string;
  query: string;  // what to pass to the search API
  radius_km: number;
  description: string;
}

export const AREAS: AreaConfig[] = [
  { slug: "rathmines",      name: "Rathmines",       query: "Rathmines, Dublin",       radius_km: 1.5, description: "a popular inner-city suburb on Dublin's southside" },
  { slug: "ranelagh",       name: "Ranelagh",         query: "Ranelagh, Dublin",        radius_km: 1,   description: "one of Dublin's most sought-after residential villages" },
  { slug: "blackrock",      name: "Blackrock",        query: "Blackrock, Dublin",       radius_km: 1.5, description: "a coastal suburb south of Dublin city centre" },
  { slug: "dun-laoghaire",  name: "Dún Laoghaire",   query: "Dún Laoghaire, Dublin",   radius_km: 2,   description: "a coastal town and harbour south of Dublin" },
  { slug: "clontarf",       name: "Clontarf",         query: "Clontarf, Dublin",        radius_km: 1.5, description: "a seaside suburb on Dublin's northside" },
  { slug: "howth",          name: "Howth",            query: "Howth, Dublin",           radius_km: 2,   description: "a picturesque fishing village and peninsula north of Dublin" },
  { slug: "malahide",       name: "Malahide",         query: "Malahide, Dublin",        radius_km: 2,   description: "a coastal village north of Dublin known for its castle and marina" },
  { slug: "stillorgan",     name: "Stillorgan",       query: "Stillorgan, Dublin",      radius_km: 1.5, description: "a suburban area in south County Dublin" },
  { slug: "sandymount",     name: "Sandymount",       query: "Sandymount, Dublin",      radius_km: 1,   description: "a coastal village close to Dublin city centre" },
  { slug: "portobello",     name: "Portobello",       query: "Portobello, Dublin",      radius_km: 1,   description: "a vibrant canalside neighbourhood in Dublin 8" },
  { slug: "galway-city",    name: "Galway City",      query: "Galway City",             radius_km: 3,   description: "the cultural capital of the west of Ireland" },
  { slug: "cork-city",      name: "Cork City",        query: "Cork City",               radius_km: 3,   description: "Ireland's second city on the River Lee" },
  { slug: "limerick-city",  name: "Limerick City",    query: "Limerick City",           radius_km: 3,   description: "a vibrant city on the River Shannon" },
  { slug: "waterford-city", name: "Waterford City",   query: "Waterford City",          radius_km: 3,   description: "Ireland's oldest city on the River Suir" },
  { slug: "kilkenny-city",  name: "Kilkenny City",    query: "Kilkenny",                radius_km: 2,   description: "the medieval capital of Ireland" },
  { slug: "drogheda",       name: "Drogheda",         query: "Drogheda, Louth",         radius_km: 2,   description: "a major town on the River Boyne in County Louth" },
  { slug: "dundalk",        name: "Dundalk",          query: "Dundalk, Louth",          radius_km: 2,   description: "the largest town in County Louth" },
  { slug: "navan",          name: "Navan",            query: "Navan, Meath",            radius_km: 2,   description: "the county town of Meath" },
  { slug: "naas",           name: "Naas",             query: "Naas, Kildare",           radius_km: 2,   description: "the county town of Kildare" },
  { slug: "bray",           name: "Bray",             query: "Bray, Wicklow",           radius_km: 2,   description: "a seaside town at the foot of the Wicklow Mountains" },
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
  D05: "Dublin 5", D06: "Dublin 6", D07: "Dublin 7", D08: "Dublin 8",
  D09: "Dublin 9", D10: "Dublin 10", D11: "Dublin 11", D12: "Dublin 12",
  D13: "Dublin 13", D14: "Dublin 14", D15: "Dublin 15", D16: "Dublin 16",
  D17: "Dublin 17", D18: "Dublin 18", D20: "Dublin 20", D22: "Dublin 22",
  D24: "Dublin 24",
};
