import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchCountySummary } from "../api";
import TrendsChart from "../components/TrendsChart";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import CountyPageTemplate from "../components/CountyPageTemplate";
import type { CountySummary } from "../types";
import { countyFromSlug, areasForCounty, provinceForCounty, PROVINCES } from "../areas";
import Breadcrumbs from "../components/Breadcrumbs";
import { usePageMeta } from "../hooks/usePageMeta";
import { getCountyContent } from "../content/counties";
import {
  getCachedCountyData,
  setCachedCountyData,
} from "../utils/countyDataCache";

function formatPrice(n: number | null) {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString("en-IE");
}

// Optional hero photo per county slug (used on the default dynamic page).
// Counties with a custom template (Cork/Galway/Dublin) manage their own imagery.
const COUNTY_HERO_IMAGES: Record<string, { src: string; alt: string; width: number; height: number }> = {
  westmeath: {
    src: "/images/westmeath-athlone-bridge.jpg",
    alt: "The town bridge over the River Shannon at Athlone, County Westmeath, with the twin towers of SS Peter and Paul's Church at sunset",
    width: 2000,
    height: 1500,
  },
  louth: {
    src: "/images/louth-boyne-cable-bridge.png",
    alt: "The Boyne Cable Bridge carrying the M1 Drogheda Bypass over the River Boyne, County Louth, seen from a riverside boardwalk",
    width: 1600,
    height: 1600,
  },
  sligo: {
    src: "/images/sligo-classiebawn-benbulben.png",
    alt: "Classiebawn Castle near Mullaghmore, County Sligo, with Benbulben mountain rising behind",
    width: 2000,
    height: 1500,
  },
  clare: {
    src: "/images/clare-burren-coast-road.jpg",
    alt: "The Burren coastal road in County Clare, with a limestone dry-stone wall and a glacial erratic boulder overlooking Galway Bay",
    width: 2000,
    height: 2000,
  },
  kerry: {
    src: "/images/kerry-mountain-pass.png",
    alt: "A mountain pass road winding through a glaciated upland valley in County Kerry, with dry-stone walls and open moorland",
    width: 2000,
    height: 661,
  },
};

// Factual overview paragraph per county slug (setting, population, area,
// county town, sites of interest). Used on the default dynamic county page.
// Cork/Galway/Dublin have custom templates with their own intro copy.
const COUNTY_INFO: Record<string, string> = {
  carlow: "County Carlow lies in the province of Leinster, in the south-east of Ireland, and is landlocked, bordered by Kilkenny, Wicklow, Wexford, Laois and Kildare. The 2022 census recorded a population of 61,931, and at 897 km² it is one of Ireland's smallest counties. Carlow town, on the River Barrow, is the county town. Notable sites include the Brownshill Dolmen, reputed to have the heaviest capstone in Europe, Carlow Castle, and St Laserian's Cathedral at Old Leighlin.",
  cavan: "County Cavan is located in the province of Ulster, in the north of Ireland, bordering Leitrim, Fermanagh, Monaghan, Meath, Longford and Westmeath. The 2022 census recorded a population of 81,704 across an area of 1,932 km². Cavan town is the county town. Known as the Lakeland County for its numerous lakes and drumlin landscape, Cavan contains the Shannon Pot, source of the River Shannon, along with Cloughoughter Castle and the Marble Arch Caves Global Geopark.",
  clare: "County Clare lies in the province of Munster, on Ireland's west coast, bounded by the Atlantic Ocean and the River Shannon estuary, and bordered by Limerick, Tipperary and Galway. The 2022 census recorded a population of 127,938 across 3,450 km². Ennis is the county town. Notable landmarks include the Cliffs of Moher, the karst landscape of the Burren, Bunratty Castle, and Loop Head, the county's westernmost point.",
  donegal: "County Donegal occupies the north-west of Ireland in the province of Ulster and is the country's northernmost county. The 2022 census recorded a population of 167,084 across 4,860 km², making it the fourth-largest county in Ireland. Lifford is the official county town, though Letterkenny is the largest settlement. Notable sites include the Slieve League cliffs, Errigal mountain, and Malin Head, the most northerly point on the island of Ireland.",
  kerry: "County Kerry lies in the province of Munster, on Ireland's south-west coast, and is the country's most westerly county, bordered by Limerick and Cork. The 2022 census recorded a population of 156,458 across 4,807 km², making it the fifth-largest county in Ireland. Tralee is the county town. Notable sites include Carrauntoohil, Ireland's highest mountain, the Lakes of Killarney, the Dingle Peninsula, and Skellig Michael, a UNESCO World Heritage Site.",
  kildare: "County Kildare lies in the province of Leinster, in the Eastern and Midland Region of Ireland. The 2022 census recorded a population of 246,977 across 1,695 km². Naas is the county town. The largely lowland county is crossed by the Barrow, Liffey and Boyne rivers, and is known for thoroughbred horse breeding and training. Notable sites include Castletown House, the Hill of Allen, and the Curragh racecourse, home to Ireland's five Classic Flat races.",
  kilkenny: "County Kilkenny lies in the province of Leinster, bordered by Tipperary, Waterford, Carlow, Wexford and Laois. The 2022 census recorded a population of 103,685, and the county covers approximately 2,073 square kilometres. Kilkenny city, on the River Nore, is the county town. Notable sites include Kilkenny Castle, St Canice's Cathedral with its round tower, Jerpoint Abbey, and Kells Priory, one of the largest medieval monastic sites in Ireland.",
  laois: "County Laois is located in the province of Leinster and is one of only two Irish counties that are doubly landlocked, bordered by Offaly, Kildare, Kilkenny, Carlow and Tipperary. Its 2022 census population was 91,657, and it covers approximately 1,720 square kilometres. Portlaoise is the county town. Notable landmarks include the Rock of Dunamase, Emo Court, the Slieve Bloom Mountains, and Timahoe Round Tower.",
  leitrim: "County Leitrim lies in the province of Connacht, bordering Donegal, Sligo, Cavan, Longford and Roscommon, with a short coastline at Tullaghan. The 2022 census recorded a population of 35,199, the smallest of any county in Connacht, across an area of approximately 1,589 square kilometres. Carrick-on-Shannon, on the River Shannon, is the county town. Notable sites include Parke's Castle on Lough Gill, Glencar Waterfall, and Lough Allen.",
  limerick: "County Limerick is situated in the province of Munster, bordering Kerry, Clare, Tipperary and Cork. The 2022 census recorded a population of 209,536, and the county covers approximately 2,756 square kilometres, ranking among the ten largest Irish counties by area. Limerick City, Ireland's third-largest city, is the county town. Notable sites include King John's Castle, Lough Gur, Adare Manor, and the Grange Stone Circle, the largest stone circle in Ireland.",
  longford: "County Longford lies in the province of Leinster, bordering Cavan, Westmeath, Roscommon and Leitrim, with Lough Ree forming part of its western boundary. The 2022 census recorded a population of 46,634, and the county covers approximately 1,091 square kilometres, making it one of the smallest counties in Ireland by area. Longford town is the county seat. Notable sites include the Corlea Trackway, the Royal Canal, and historic monastic sites at Ardagh and Abbeylara.",
  louth: "County Louth lies in the province of Leinster, on Ireland's east coast, bordering Meath, Monaghan, Armagh and Down. At approximately 826 square kilometres, it is the smallest county in Ireland by land area, while the 2022 census recorded a population of 139,100. Dundalk is the county town. Notable sites include Mellifont Abbey, Monasterboice with its high crosses, Carlingford Lough, and King John's Castle in Carlingford.",
  mayo: "County Mayo lies in the west of Ireland, in the province of Connacht, bordered by the Atlantic Ocean, County Galway, County Roscommon and County Sligo. At the 2022 census it had a population of 137,231 across 5,588 km², making it the third-largest county in Ireland by area. Castlebar is the county town. Landmarks include Croagh Patrick, the Neolithic Céide Fields, Knock Shrine and Achill Island.",
  meath: "County Meath lies in east-central Ireland, in the province of Leinster, within the Eastern and Midland Region. The 2022 census recorded a population of 220,826 across an area of 2,342 km², roughly the eleventh-largest of Ireland's 26 counties. Navan is the county town, having replaced Trim in 1898. Notable sites include the Newgrange passage tomb at Brú na Bóinne, the Hill of Tara, Trim Castle and the Abbey of Kells.",
  monaghan: "County Monaghan is located in the province of Ulster, forming part of the Border area within the Northern and Western Region of Ireland. Its 2022 census population was 65,288, spread over 1,295 km², one of the smaller counties in area. Monaghan town is the county seat. Sites of interest include Slieve Beagh, Clones Round Tower, Castle Leslie in Glaslough and Monaghan County Museum, an award-winning provincial museum.",
  offaly: "County Offaly sits in Ireland's midlands, in the province of Leinster, bordering seven other counties including Galway, Tipperary and Meath. At the 2022 census its population stood at 82,668, over an area of 2,001 km². Tullamore is the county town. Landmarks include the monastic site of Clonmacnoise on the River Shannon, Birr Castle with its 19th-century Leviathan telescope, and the Slieve Bloom Mountains, whose highest point, Arderin, reaches 527 metres.",
  roscommon: "County Roscommon lies in the province of Connacht, in the midwest of Ireland; the geographical centre of Ireland lies on the western shore of Lough Ree, in the south of the county. The 2022 census recorded a population of 70,259 across 2,548 km², making it around the ninth-largest of Ireland's 26 counties. Roscommon town is the county town. Sites of interest include the Rathcroghan archaeological complex, Lough Key Forest Park, Boyle Abbey and Strokestown Park.",
  sligo: "County Sligo lies in the northwest of Ireland, in the province of Connacht, bordered by Mayo, Roscommon and Leitrim. The 2022 census recorded a population of 70,198 across an area of 1,838 km². Sligo town, with 20,608 residents, is the county town and largest settlement. Notable landmarks include Benbulben mountain, the Carrowmore Megalithic Cemetery, Lough Gill (associated with poet W.B. Yeats) and the passage tomb atop Knocknarea.",
  tipperary: "County Tipperary lies in the province of Munster and is the largest landlocked county in Ireland, bordering eight other counties. The 2022 census recorded a population of 167,895 across an area of 4,305 km². Clonmel and Nenagh have historically served as joint county towns. Notable sites include the Rock of Cashel, seat of the ancient Kings of Munster, Galtymore mountain, and Coolmore Stud, one of the world's largest thoroughbred breeding operations.",
  waterford: "County Waterford lies on the south coast of Ireland, in the province of Munster. The 2022 census recorded a population of 127,363 across an area of 1,858 km². Waterford city is the county town. Notable sites include the Copper Coast, a UNESCO Global Geopark, the Woodstown Viking settlement near the Suir estuary, and the Ballynageeragh portal tomb, a megalithic structure dating to the 4th millennium BC.",
  westmeath: "County Westmeath lies in the midlands of Ireland, within the province of Leinster, and is a landlocked county known for its lakes. The 2022 census recorded a population of 95,840 across an area of 1,840 km². Mullingar is the county town. Notable sites include the Hill of Uisneach, regarded as the traditional geographical centre of Ireland, the Royal Canal, Lough Ennell, and Mullingar's Christ the King Cathedral.",
  wexford: "County Wexford occupies the south-east corner of Ireland, in the province of Leinster, with coastlines on the Irish Sea and Celtic Sea. The 2022 census recorded a population of 163,527 across an area of 2,367 km². Wexford town is the county town. Notable sites include Hook Head Lighthouse, Dunbrody Abbey, Enniscorthy Castle, and the Irish National Heritage Park at Ferrycarrig.",
  wicklow: "County Wicklow lies in the province of Leinster, immediately south of Dublin, with the Irish Sea to its east and the Wicklow Mountains forming much of its interior. The 2022 census recorded a population of 155,851 across an area of 2,027 km². Wicklow town is the county town. Notable sites include Glendalough monastic settlement, Powerscourt Waterfall, and Wicklow Mountains National Park. The county is nicknamed 'the Garden of Ireland'.",
};

export default function CountyPage() {
  const { slug } = useParams<{ slug: string }>();
  const county = countyFromSlug(slug ?? "");

  // Check if we have custom content for this county
  const customContent = getCountyContent(slug ?? "");

  // If custom content exists, use the template
  if (customContent) {
    return <CountyPageTemplate content={customContent} />;
  }

  // Otherwise, fall back to the default dynamic page
  const [data, setData] = useState<CountySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!county) return;

    // Try cache first
    const cached = getCachedCountyData(county);

    if (cached) {
      setData(cached);
      setLoading(false);
    } else {
      setLoading(true);
      fetchCountySummary(county)
        .then((freshData) => {
          setData(freshData);
          setCachedCountyData(county, freshData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [county, slug]);

  if (!county) return (
    <>
      <PageHeader title="County not found" />
      <div className="content-page"><h1>County not found</h1></div>
    </>
  );

  const meta = usePageMeta(
    county ? `Property Prices in County ${county}` : undefined,
    county ? `Browse every residential sale in County ${county} since 2010. View price trends, median values, and recent sales from Ireland's Property Price Register.` : undefined,
    county ? [{ name: "Area Guides", url: "/areaguides" }, { name: `County ${county}`, url: `/county/${slug ?? ""}` }] : undefined,
  );

  const latestTrend = data?.trends[data.trends.length - 1];
  const earliestTrend = data?.trends[0];

  const slugStr = slug ?? "";
  const countyAreas = areasForCounty(slugStr);
  const province = provinceForCounty(slugStr);
  const siblingCountySlugs = province
    ? (PROVINCES.find(p => p.name === province)?.counties ?? []).filter(s => s !== slugStr)
    : [];

  return (
    <>
      {meta}
      <PageHeader title={`Property Prices in County ${county}`} titleAsHeading={false} />
      <div className="content-page">
      <Breadcrumbs items={[{ name: "Area Guides", url: "/areaguides" }, { name: `County ${county}`, url: `/county/${slugStr}` }]} />
      <h1>Property Prices in County {county}</h1>
      {COUNTY_HERO_IMAGES[slugStr] && (
        <img
          className="area-hero"
          src={COUNTY_HERO_IMAGES[slugStr].src}
          alt={COUNTY_HERO_IMAGES[slugStr].alt}
          width={COUNTY_HERO_IMAGES[slugStr].width}
          height={COUNTY_HERO_IMAGES[slugStr].height}
          loading="lazy"
        />
      )}
      <p className="content-intro">
        Explore residential property sale prices across County {county} from{" "}
        <Link to="/property-price-register" style={{ color: "#1a3c5e", textDecoration: "underline" }}>
          Ireland's Property Price Register
        </Link>. Every sale since 2010 is included.
      </p>

      {COUNTY_INFO[slugStr] && (
        <p className="area-info">{COUNTY_INFO[slugStr]}</p>
      )}

      {loading && <div className="content-loading">Loading data…</div>}
      {error && <div className="error-msg">{error}</div>}

      {data && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <span>Median price ({latestTrend?.year ?? "latest"})</span>
              <strong>{formatPrice(latestTrend?.median_price ?? null)}</strong>
            </div>
            <div className="stat-card">
              <span>Average price ({latestTrend?.year ?? "latest"})</span>
              <strong>{formatPrice(latestTrend?.avg_price ?? null)}</strong>
            </div>
            <div className="stat-card">
              <span>Total sales on record</span>
              <strong>{data.total_count.toLocaleString()}</strong>
            </div>
            <div className="stat-card">
              <span>Data from</span>
              <strong>{earliestTrend?.year ?? "—"} – {latestTrend?.year ?? "—"}</strong>
            </div>
          </div>

          {data.trends.length > 0 && (
            <section className="content-section">
              <h2>House Price Trends in County {county}</h2>
              <p>
                Median and average residential sale prices in County {county} by year,
                based on full market price sales only.
              </p>
              <div style={{ position: "relative", height: 240 }}>
                <TrendsChart data={data.trends} onClose={() => {}} inline />
              </div>
            </section>
          )}

          {data.trends.length > 1 && latestTrend && earliestTrend && (
            <section className="content-section">
              <h2>How Have Prices Changed?</h2>
              <p>
                The median sale price in County {county} was{" "}
                <strong>{formatPrice(earliestTrend.median_price)}</strong> in {earliestTrend.year},
                rising to <strong>{formatPrice(latestTrend.median_price)}</strong> in {latestTrend.year}.
              </p>
            </section>
          )}

          {data.recent.length > 0 && (
            <section className="content-section">
              <h2>Recent Sales in County {county}</h2>
              <table className="sales-table">
                <thead>
                  <tr><th>Address</th><th>Date</th><th>Price</th></tr>
                </thead>
                <tbody>
                  {data.recent.map(p => (
                    <tr key={p.id}>
                      <td>{p.address}</td>
                      <td>{p.sale_date.slice(0, 10)}</td>
                      <td>{formatPrice(p.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {countyAreas.length > 0 && (
            <section className="content-section">
              <h2>Areas in County {county}</h2>
              <div className="areas-grid">
                {countyAreas.map(area => (
                  <Link key={area.slug} to={`/area/${area.slug}`} className="area-card">
                    <h3>{area.name}</h3>
                    <p>{area.description}</p>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {siblingCountySlugs.length > 0 && (
            <section className="content-section">
              <h2>Nearby Counties in {province}</h2>
              <div className="county-links">
                {siblingCountySlugs.map(sib => (
                  <Link key={sib} to={`/county/${sib}`} className="county-link-btn">
                    County {countyFromSlug(sib) ?? sib}
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="content-section">
            <h2>Search County {county} Properties</h2>
            <p>
              Use the <Link to={`/?q=${encodeURIComponent(county)}&county=${encodeURIComponent(county)}`}>interactive map</Link> to
              search by address or Eircode within County {county}.
            </p>
            <p>
              Browse <Link to="/areaguides">all area guides</Link>.
            </p>
          </section>
        </>
      )}
      <Footer />
    </div>
    </>
  );
}
