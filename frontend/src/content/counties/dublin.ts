import type { CountyContent } from "../countyData";

export const dublinContent: CountyContent = {
  name: "Dublin",
  slug: "dublin",

  metaTitle: "Dublin Property Prices 2026 & Market Trends",
  metaDescription: "Dublin property prices in 2026: median around €478,000. Explore price trends, transaction volumes, and recent sales from Ireland's Property Price Register — Rathmines, Ranelagh, Blackrock, Clontarf and more.",

  intro: "Dublin remains Ireland's most expensive property market. In 2025, the last complete year, the median residential sale price in County Dublin reached €475,000 with an average of roughly €609,000 across more than 18,000 transactions. Prices have continued to climb into 2026, with the year-to-date median running near €478,000 and the average around €616,000. As the capital and most populous county — home to about 1.5 million people — Dublin combines the country's strongest jobs market with a persistent shortage of housing supply, keeping upward pressure on prices. The county spans everything from Georgian townhouses and Victorian redbricks in the inner city to coastal homes in Howth, Malahide and Dalkey and family estates across the commuter suburbs. Since 2010, when the Dublin median sat at €270,000, prices have risen more than 75%, recovering fully from the post-crash trough and pushing well beyond previous peaks.",

  marketOverview: "Dublin's market is defined by strong demand meeting constrained supply. The tech and financial-services sectors clustered around the Docklands (Dublin 2 and 4) and the wider city underpin high-paying employment that feeds buyer demand, while national schemes such as Help-to-Buy and the First Home Scheme add further competition for new and mid-market homes. The traditional divide between a more expensive southside and a more affordable northside still holds broadly: Dublin 4 (Ballsbridge, Sandymount), Dublin 6 (Rathmines, Ranelagh) and coastal south-county areas like Blackrock, Dún Laoghaire and Dalkey command the highest prices, while northside districts and outer suburbs offer relatively better value. Apartments and smaller homes dominate the inner-city and Docklands markets, appealing to professionals and investors, whereas semi-detached and detached family homes drive demand in suburbs such as Clontarf, Malahide, Stillorgan and Castleknock. Outer commuter zones and the fringes of the county remain the entry points for first-time buyers priced out of the core. Low transaction volumes relative to demand, combined with limited new-build completions, continue to shape a competitive, fast-moving market in 2026.",

  trendsCommentary: "Dublin property prices have risen steadily since the 2012–2013 trough, with the median climbing from €270,000 in 2010 to €475,000 in 2025. Growth accelerated through the 2020–2025 period despite higher interest rates, as supply failed to keep pace with population and employment growth. The 2025 full-year median of €475,000 gave way to a 2026 year-to-date figure near €478,000, signalling continued but more moderate appreciation. Coastal and established southside areas have consistently outperformed, while the largest gains in percentage terms have often come from more affordable northside and commuter districts as buyers chase value. Average prices sit well above the median — around €616,000 in 2026 — reflecting a long tail of high-value sales in premium neighbourhoods.",

  popularAreas: [
    {
      name: "Rathmines",
      slug: "rathmines",
      description: "Popular inner-city suburb on Dublin's southside, redbrick terraces and apartments"
    },
    {
      name: "Ranelagh",
      slug: "ranelagh",
      description: "One of Dublin's most sought-after residential villages, period homes"
    },
    {
      name: "Blackrock",
      slug: "blackrock",
      description: "Coastal south-county suburb, upscale family homes and villages"
    },
    {
      name: "Dún Laoghaire",
      slug: "dun-laoghaire",
      description: "Coastal town and harbour, period houses and seafront apartments"
    },
    {
      name: "Clontarf",
      slug: "clontarf",
      description: "Seaside suburb on the northside, family homes near the coast"
    },
    {
      name: "Howth",
      slug: "howth",
      description: "Picturesque fishing village and peninsula north of the city"
    },
    {
      name: "Malahide",
      slug: "malahide",
      description: "Coastal village known for its castle and marina, family estates"
    },
    {
      name: "Sandymount",
      slug: "sandymount",
      description: "Coastal village close to the city centre in Dublin 4"
    }
  ],

  faqs: [
    {
      question: "What is the average house price in Dublin in 2026?",
      answer: "In 2026 the average residential sale price in County Dublin is around €616,000, with a median of roughly €478,000 (year to date). The median — the midpoint price — is a better guide for typical buyers, as the higher average is pulled up by premium sales in areas like Dublin 4 and Dalkey. Prices vary widely by area, from inner-city apartments to multi-million-euro coastal homes."
    },
    {
      question: "How much have Dublin property prices risen since 2010?",
      answer: "The median Dublin sale price has risen from €270,000 in 2010 to €475,000 in 2025 — an increase of more than 75%. Prices fell in 2011–2013 following the financial crisis before recovering strongly from 2014 onwards, and have continued rising into 2026 despite higher mortgage rates."
    },
    {
      question: "Which areas of Dublin are most expensive?",
      answer: "The most expensive areas are generally on the southside and along the coast: Dublin 4 (Ballsbridge, Sandymount), Dublin 6 (Rathmines, Ranelagh, Rathgar), and south-county coastal areas such as Blackrock, Dún Laoghaire and Dalkey. These areas regularly see prices well above the county median. Northside and outer commuter districts typically offer better value."
    },
    {
      question: "Which areas of Dublin are more affordable?",
      answer: "More affordable options are typically found in northside districts and outer suburbs, as well as on the western and northern fringes of the county. First-time buyers often look to these areas, and to neighbouring commuter counties like Meath, Kildare and Wicklow, where prices are lower than in Dublin's core."
    },
    {
      question: "Is Dublin a good place to invest in property?",
      answer: "Dublin has strong long-term fundamentals: it is Ireland's economic centre, with a large tech and financial-services sector, a growing population, and persistent housing undersupply that supports both rental demand and capital values. However, entry prices are high and yields vary by area, so location and property type selection are important. As with any investment, past price growth does not guarantee future returns."
    },
    {
      question: "What types of property are common in Dublin?",
      answer: "Dublin has a diverse housing stock. The inner city and Docklands feature Georgian townhouses, Victorian redbricks and modern apartments. Suburbs are dominated by semi-detached and detached family homes built from the mid-20th century onwards. Coastal areas mix period houses, seafront apartments and modern developments. Apartments make up a large share of sales in the city centre, while houses dominate the suburbs and commuter belt."
    }
  ],

  neighboringCounties: ["meath", "kildare", "wicklow"],

  highlights: [
    "Ireland's capital and most populous county (~1.5 million people)",
    "Strongest jobs market in the country, led by tech and financial services",
    "2025 median €475,000; 2026 year-to-date median near €478,000",
    "Persistent housing undersupply keeps upward pressure on prices",
    "Coastal southside and city-centre areas command the highest prices"
  ]

  // heroImages: [
  //   // TODO: Add working image URLs (Unsplash or locally stored Wikimedia)
  // ]
};
