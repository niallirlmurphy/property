export interface AreaConfig {
  slug: string;
  name: string;
  query: string;  // what to pass to the search API
  radius_km: number;
  description: string;
  county: string;  // parent county slug (e.g. "dublin", "cork")
  info?: string;   // one-paragraph factual overview (setting, population, landmarks)
  image?: string;  // optional hero photo path under /images (public/)
  imageAlt?: string; // alt text for the hero photo
}

export const AREAS: AreaConfig[] = [
  { slug: "rathmines", name: "Rathmines", query: "Rathmines, Dublin", radius_km: 1.5, description: "a popular inner-city suburb on Dublin's southside", county: "dublin",
    info: "Rathmines is an inner southside suburb of Dublin, in postal district Dublin 6, bounded to the north by the Grand Canal, long known for its density of subdivided Georgian and Victorian houses. Landmarks include Rathmines Town Hall, whose clock tower is nicknamed the 'Four Faced Liar', the domed Church of Mary Immaculate Refuge of Sinners, the Carnegie-funded Rathmines Library, and the Stella Cinema." },
  { slug: "ranelagh", name: "Ranelagh", query: "Ranelagh, Dublin", radius_km: 1, description: "one of Dublin's most sought-after residential villages", county: "dublin",
    info: "Ranelagh is an affluent residential area and urban village on Dublin's southside, in postal district Dublin 6, originally known as Cullenswood before its 19th-century development. Landmarks include Ranelagh Gardens, an 18th-century pleasure ground where Richard Crosbie made Ireland's first hot air balloon flight in 1785, the Ranelagh Arts Centre, and Scoil Bhríde, the first gaelscoil (Irish-language school) in Ireland, founded in 1917. Two Luas tram stops serve the village." },
  { slug: "blackrock", name: "Blackrock", query: "Blackrock, Dublin", radius_km: 1.5, description: "a coastal suburb south of Dublin city centre", county: "dublin",
    info: "Blackrock is an affluent coastal suburb in Dún Laoghaire-Rathdown, on Dublin Bay about 3km northwest of Dún Laoghaire. Its electoral division recorded a population of 31,152 in Census 2022. The area grew after Blackrock railway station opened in 1834, the oldest in Ireland, with DART services now linking it to the city centre in about 15 minutes. Landmarks include Blackrock Park, site of an early 19th-century Martello tower, and Blackrock Market." },
  { slug: "dun-laoghaire", name: "Dún Laoghaire", query: "Dún Laoghaire, Dublin", radius_km: 2, description: "a coastal town and harbour south of Dublin", county: "dublin",
    info: "Dún Laoghaire is a coastal town on Dublin's southside, its name meaning 'fort of Laoghaire' after a 5th-century High King. Census 2022 recorded 31,239 residents, up from 26,525 in 2016. The town is built around a harbour with two granite piers dating from 1817 to 1859, including the popular East Pier, and hosts an 820-berth marina, the largest in Ireland, plus the National Maritime Museum.",
    image: "/images/dun-laoghaire-harbour.jpg", imageAlt: "A dinghy sailing in Dún Laoghaire harbour, with the town and the spire of the Mariners' Church (National Maritime Museum) behind" },
  { slug: "clontarf", name: "Clontarf", query: "Clontarf, Dublin", radius_km: 1.5, description: "a seaside suburb on Dublin's northside", county: "dublin",
    info: "Clontarf is an affluent coastal suburb on Dublin's northside, in postal district Dublin 3, fronting Dublin Bay with a promenade running 4.5km to Dollymount. It was the site of the Battle of Clontarf in 1014, in which Brian Boru's forces defeated a Viking and Leinster alliance. Landmarks include Clontarf Castle, St Anne's Park, and North Bull Island, home to two golf courses, a nature reserve, and a replica Easter Island moai.",
    image: "/images/clontarf-harbour.jpg", imageAlt: "Sailboats moored on Dublin Bay off Clontarf, with Howth Head in the distance" },
  { slug: "howth", name: "Howth", query: "Howth, Dublin", radius_km: 2, description: "a picturesque fishing village and peninsula north of Dublin", county: "dublin",
    info: "Howth is a peninsular fishing village and outer suburb of Dublin, roughly 14km northeast of the city centre on Howth Head, which forms the northern edge of Dublin Bay. Census 2022 recorded an urban population of 8,399. It remains a tier-2 fishing port with an active harbour and marina. Landmarks include Howth Castle, the adjacent Aideen's Grave dolmen, the Bailey Lighthouse, a 6km cliff path loop, and the offshore island of Ireland's Eye." },
  { slug: "malahide", name: "Malahide", query: "Malahide, Dublin", radius_km: 2, description: "a coastal village north of Dublin known for its castle and marina", county: "dublin",
    info: "Malahide is a coastal settlement roughly 14km north of Dublin city, with a village centre bordered by suburban housing and an estuary where the Broadmeadow River meets the sea. Census 2022 recorded a population of 18,608. The area is dominated by Malahide Castle, dating from the 12th century, set within a demesne that includes an international cricket ground. A marina and sandy beach line the shorefront." },
  { slug: "stillorgan", name: "Stillorgan", query: "Stillorgan, Dublin", radius_km: 1.5, description: "a suburban area in south County Dublin", county: "dublin",
    info: "Stillorgan is a suburban area in Dun Laoghaire-Rathdown, south Co. Dublin, with a population of 18,212 recorded in the 2022 census. Once a village in its own right, it retains an old village centre alongside later housing estates. Notable features include the 18th-century Stillorgan Obelisk, designed by Edward Lovett Pearce, and Stillorgan Shopping Centre, which opened in 1966 as Ireland's first shopping centre." },
  { slug: "sandymount", name: "Sandymount", query: "Sandymount, Dublin", radius_km: 1, description: "a coastal village close to Dublin city centre", county: "dublin",
    info: "Sandymount is a coastal suburb in the Dublin 4 district, three to four kilometres south-east of Dublin city centre. The area is fronted by Sandymount Strand, an extensive beach forming part of the southern shore of Dublin Bay, and includes a Martello tower built as part of early 19th-century coastal defences against a feared Napoleonic invasion. Sandymount Green, a triangular park bordered by shops and cafes, sits at the centre of the village.",
    image: "/images/sandymount-strand-sunset.jpg", imageAlt: "Sunset over Sandymount Strand at low tide, with the Poolbeg chimneys and Dublin Port cranes on the horizon reflected in the wet sand" },
  { slug: "portobello", name: "Portobello", query: "Portobello, Dublin", radius_km: 1, description: "a vibrant canalside neighbourhood in Dublin 8", county: "dublin",
    info: "Portobello is a canalside neighbourhood in Dublin's southern city centre, bounded to the south by the Grand Canal. It expanded as a suburb through the 18th and 19th centuries and, from the late 19th century, became known as Dublin's \"Little Jerusalem\" after Ashkenazi Jewish families settled there; the Irish Jewish Museum on Walworth Road records this history. Other landmarks include Portobello Barracks, built 1810-1815, and La Touche Bridge over the canal." },
  { slug: "galway-city", name: "Galway City", query: "Galway City", radius_km: 3, description: "the cultural capital of the west of Ireland", county: "galway",
    info: "Galway City lies on Ireland's west coast where the River Corrib flows between Lough Corrib and Galway Bay, and recorded a population of 85,910 in the 2022 census, the state's fourth most populous urban area. The medieval core includes the Spanish Arch, built in 1519-20, and Lynch's Castle, a 16th-century townhouse on Shop Street. St Nicholas' Collegiate Church, founded in 1320, and the Claddagh, a historic fishing quarter, are also notable." },
  { slug: "salthill", name: "Salthill", query: "Salthill, Galway", radius_km: 1.5, description: "a seaside suburb of Galway city with a popular promenade", county: "galway",
    info: "Salthill is a seaside suburb to the south-west of Galway city centre, on the shore of Galway Bay; the 2016 census recorded a population of 3,650. Developed as a Victorian bathing resort, it retains a two-kilometre promenade, known locally as \"the Prom\", opened in 1856. Other landmarks include the Blackrock diving tower, built in 1953 and used for Christmas Day swimming, and Pearse Stadium, a Galway GAA venue." },
  { slug: "oranmore", name: "Oranmore", query: "Oranmore, Galway", radius_km: 2, description: "a growing commuter town east of Galway city", county: "galway",
    info: "Oranmore is a town on an inlet of Galway Bay, roughly 9km east of Galway city, County Galway. The 2022 census recorded a population of 5,819, reflecting steady growth as a commuter base for Galway city. Landmarks include the 15th-century Oranmore Castle, medieval church ruins with a gravestone dated 1661, and St Mary's Church, built in 1803 and now the town library." },
  { slug: "athenry", name: "Athenry", query: "Athenry, Galway", radius_km: 2, description: "a historic walled town in County Galway", county: "galway",
    info: "Athenry is a medieval town in County Galway, some 25km east of Galway city, notable for retaining around 70% of its original town wall circuit. The 2022 census recorded a population of 4,603. Landmarks include Athenry Castle, built before 1240; the 13th-century Dominican Priory; and the late 15th-century Market Cross, the only medieval cross still standing in its original position in Ireland." },
  { slug: "tuam", name: "Tuam", query: "Tuam, Galway", radius_km: 2, description: "a market town in north County Galway", county: "galway",
    info: "Tuam is a market town in north County Galway, about 35km north of Galway city, and an ecclesiastical centre tracing its origins to a monastic settlement founded by St Jarlath. The 2022 census recorded a population of 9,647. Landmarks include the Cathedral of the Assumption (1827-1837), St Mary's Cathedral, which houses the High Cross of Tuam dated to 1152, the ruins of Temple Jarlath, and the Mill Museum's restored waterwheel." },
  { slug: "connemara", name: "Connemara", query: "Clifden, Galway", radius_km: 5, description: "a scenic rural region on Galway's western coast", county: "galway",
    info: "Connemara is a rugged coastal region in west County Galway, characterised by mountains including the Twelve Bens, blanket bog, small lakes and an indented Atlantic shoreline. Its principal town, Clifden, recorded a population of 1,259 at the 2022 census. Notable sites include Connemara National Park, Kylemore Abbey, the ruined Clifden Castle, and the Sky Road, an 11km scenic coastal route." },
  { slug: "cork-city", name: "Cork City", query: "Cork City", radius_km: 3, description: "Ireland's second city on the River Lee", county: "cork",
    info: "Cork is Ireland's second-largest city, built on an island between two channels of the River Lee before they converge into Cork Harbour. The 2022 census recorded a population of 224,004 within the city boundary. Landmarks include St Fin Barre's Cathedral, the English Market, trading since 1610, St Anne's Church in Shandon, and University College Cork, whose grounds border the river." },
  { slug: "douglas", name: "Douglas", query: "Douglas, Cork", radius_km: 1.5, description: "an upscale suburb on Cork city's southside", county: "cork",
    info: "Douglas is a suburb with a village core on the southside of Cork city, formally incorporated into the Cork City Council area in May 2019. At the 2016 census, the Douglas electoral division recorded a population of approximately 26,883. Landmarks include Douglas Village Shopping Centre, opened in the mid-1970s and described as Ireland's second shopping centre, St Luke's Church (1875), and Ballybrack Woods." },
  { slug: "ballincollig", name: "Ballincollig", query: "Ballincollig, Cork", radius_km: 2, description: "a large commuter town west of Cork city", county: "cork",
    info: "Ballincollig is a town on the River Lee to the west of Cork city, brought within the Cork City Council boundary in 2019. At the 2016 census, the Ballincollig electoral division recorded a population of 18,621, then the largest town in County Cork. Landmarks include Ballincollig Regional Park, a 135-acre site incorporating the former Royal Gunpowder Mills, established in 1794, and the ruined Ballincollig Castle." },
  { slug: "carrigaline", name: "Carrigaline", query: "Carrigaline, Cork", radius_km: 2, description: "a growing town south of Cork city", county: "cork",
    info: "Carrigaline is a town on the River Owenabue in County Cork, roughly 12km south of Cork city, functioning as one of the county's largest commuter towns. Census 2022 recorded a population of 18,239, up 15.7% from 2016. Landmarks include St Mary's Church (1824), Our Lady and John Church (1957), and the former Carrigaline Pottery on Main Street. The town also serves as a gateway to West Cork." },
  { slug: "cobh", name: "Cobh", query: "Cobh, Cork", radius_km: 2, description: "a historic port town on Cork harbour", county: "cork",
    info: "Cobh is a seaport town on Great Island in Cork Harbour, County Cork, known for its Victorian terraces, including the colourful row nicknamed the 'deck of cards', beneath St Colman's Cathedral. Census 2022 recorded a population of 14,148. Formerly Queenstown, it was the Titanic's final port of call in 1912 and a major 19th-century emigration point. Sites include the Cobh Heritage Centre, Titanic Experience Museum, and nearby Spike Island." },
  { slug: "midleton", name: "Midleton", query: "Midleton, Cork", radius_km: 2, description: "a market town and distillery gateway in East Cork", county: "cork",
    info: "Midleton is a market town in East Cork, about 16km east of Cork city, serving as the commercial hub of the area. Census 2022 recorded a population of 13,906, roughly double its 1996 figure. It is home to the Old Midleton Distillery, founded in 1825 and now housing the Jameson Experience visitor centre, which contains the world's largest pot still and Ireland's largest working waterwheel. Midleton Library dates to 1789." },
  { slug: "kinsale", name: "Kinsale", query: "Kinsale, Cork", radius_km: 2, description: "a coastal gourmet destination and sailing hub in County Cork", county: "cork",
    info: "Kinsale is a harbour town on the River Bandon estuary in County Cork, around 25km south of Cork city, noted for its narrow streets and colourfully painted shopfronts. Census 2022 recorded a population of 5,991. Historic sites include Charles Fort (1677), James Fort (1607), and Desmond Castle, a 16th-century tower house. The town is known for its restaurant scene and active sailing community centred on Kinsale Yacht Club.",
    image: "/images/kinsale-charles-fort.jpg", imageAlt: "The classical entrance gateway and wooden footbridge of Charles Fort, the 17th-century star fort overlooking Kinsale harbour in County Cork" },
  { slug: "limerick-city", name: "Limerick City", query: "Limerick City", radius_km: 3, description: "a vibrant city on the River Shannon", county: "limerick",
    info: "Limerick is a city on the River Shannon in County Limerick, with its historic core on King's Island where the river meets the Abbey River. Census 2022 recorded an urban population of 102,287, the third-largest in the Republic of Ireland. Landmarks include King John's Castle (1210), St Mary's Cathedral (1168), the Hunt Museum, and the Treaty Stone, linked to the 1691 Treaty of Limerick, on Clancy Strand." },
  { slug: "waterford-city", name: "Waterford City", query: "Waterford City", radius_km: 3, description: "Ireland's oldest city on the River Suir", county: "waterford",
    info: "Waterford is a city on the River Suir in County Waterford, founded by Vikings in 914 AD and considered Ireland's oldest city. Census 2022 recorded a population of 60,079, the fifth-largest in the state. Reginald's Tower, a 13th-14th century structure retaining its Norse name, is the oldest urban civic building in Ireland and now houses a museum. The city is historically associated with Waterford Crystal, produced there since 1783." },
  { slug: "kilkenny-city", name: "Kilkenny City", query: "Kilkenny", radius_km: 2, description: "the medieval capital of Ireland", county: "kilkenny",
    info: "Kilkenny is a city on the River Nore in County Kilkenny, set in a sheltered valley in Ireland's south-east. Census 2022 recorded a population of 27,184. Its medieval core, known as the Medieval Mile, includes surviving city walls and gates such as Talbot Tower. Kilkenny Castle, begun in 1204, overlooks the river, while St Canice's Cathedral stands beside a 9th-century round tower on the city's original monastic site." },
  { slug: "drogheda", name: "Drogheda", query: "Drogheda, Louth", radius_km: 2, description: "a major town on the River Boyne in County Louth", county: "louth",
    info: "Drogheda is a port town on the River Boyne in County Louth, about 43 km north of Dublin, with a population of 44,135 at the 2022 Census. It occupies the river's lowest crossing point before the Boyne meets the Irish Sea. Medieval remains include St Laurence's Gate and Millmount, a Norman motte housing a museum; the Highlanes Gallery occupies a former Franciscan church, and Newgrange lies about 8 km west." },
  { slug: "dundalk", name: "Dundalk", query: "Dundalk, Louth", radius_km: 2, description: "the largest town in County Louth", county: "louth",
    info: "Dundalk is the largest town in County Louth, midway between Dublin and Belfast and close to the border with Northern Ireland. Its 2022 Census population was 43,112 in the urban area, or 64,287 across the wider municipal district. The town developed from a Norman stronghold into a 19th-century manufacturing centre. Landmarks include the County Museum in a former distillery, Castle Roche, Oriel Park, and the nearby Proleek Dolmen." },
  { slug: "navan", name: "Navan", query: "Navan, Meath", radius_km: 2, description: "the county town of Meath", county: "meath",
    info: "Navan is the county town of Meath, situated at the confluence of the Rivers Boyne and Blackwater about 50 km northwest of Dublin. Its population at the 2022 Census was 33,886. The town's layout dates to Norman times, though most surviving buildings are Victorian or Edwardian. Landmarks include Athlumney Castle, St Mary's Church, Navan Town Hall, and Pairc Tailteann, home ground of Meath's Gaelic football and hurling teams." },
  { slug: "naas", name: "Naas", query: "Naas, Kildare", radius_km: 2, description: "the county town of Kildare", county: "kildare",
    info: "Naas is the county town of Kildare, in Leinster, with a population of 26,180 at the 2022 Census, making it the fourteenth-largest urban centre in Ireland. Originally a medieval walled market town, it now serves as a centre for local administration and commerce. Sites of interest include Naas Racecourse, Naas Town Hall (built in 1796 as a gaol), St David's Church, and the Grand Canal, which runs through the town." },
  { slug: "bray", name: "Bray", query: "Bray, Wicklow", radius_km: 2, description: "a seaside town at the foot of the Wicklow Mountains", county: "wicklow",
    info: "Bray is a coastal town in County Wicklow, about 20 km south of Dublin at the foot of the Wicklow Mountains, with a population of 33,512 at the 2022 Census. Developed as a seaside resort after the railway arrived in 1854, it has a long promenade fronting a beach of sand and shingle. Landmarks include Bray Head, a 241-metre headland with walking trails, Killruddery House, and Ardmore Studios." },
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
