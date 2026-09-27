# IRES REIT — Portfolio Valuation (IRES-owned units)

**Method:** HomeIQ valuation pipeline (`POST /valuation/estimate` internals) run per
development × bedroom type, driven by an explicit coordinate per development.
**Comparables:** PPR resale sales within an adaptive 1–20 km radius, last 3 years,
time-adjusted to today via county price indices, then weighted by distance + recency +
bedroom match + **property-type match** (apartment vs house). Local price outliers are
trimmed, a **bedroom price ladder** normalises every comparable to a 2-bed-equivalent, and
an **apartment-price ceiling** (learned from confirmed local apartment sales) excludes
house-priced comparables. Bulk/multi-unit rows and out-of-band prices are excluded.
**Valued:** 2026-09-27 · **Source portfolio:** `docs/ires_reit_portfolio.md`
**Raw output:** `docs/ires_valuation_raw.json`

## Headline

| | |
|---|---|
| Developments | 35 |
| IRES-owned units valued | 3,615 |
| **Estimated gross value** | **€1,522,863,679** (≈ €1.52 bn) |
| Average per unit | €421,262 |
| Rows valued | 106 / 106 bedroom-type rows |

> ⚠️ **Read this as an indicative model estimate, not a valuation of record.** It is
> built from open-market PPR *resale* comparables, so it reflects what comparable
> second-hand homes near each scheme have sold for — not IRES's book value, not a
> block/portfolio (bulk-discounted) value, and not rental/investment (yield) value. A
> real institutional block would typically transact **below** the sum-of-units figure.

### What changed in this run

Three model improvements and a coordinate audit brought the headline down from the earlier
~€2.0 bn run and removed the implausible seven-figure apartment values it contained:

1. **Bedroom price ladder.** Every comparable is normalised to a "2-bed-equivalent" using
   Dublin apartment bedroom ratios (1-bed 0.80 · 2-bed 1.00 · 3-bed 1.28 · 4-bed 1.50),
   producing one base per location that is re-expanded to each bedroom count. This
   guarantees a larger unit is never valued below a smaller one at the same location.
2. **Local outlier trim.** A Tukey IQR fence removes lone extreme sales (a trophy home or a
   multi-unit deal recorded amid ordinary sales) before weighting.
3. **Apartment-price ceiling.** For apartment subjects the model learns what an apartment
   actually costs locally (Tukey far-outlier fence on confirmed nearby apartment sales,
   2-bed-equivalent) and drops comparables priced like houses — the pricey, often
   *unlabelled* houses that dominate house-heavy areas and previously inflated apartment
   schemes (e.g. Phoenix Park Racecourse fell from a false €0.87m/2-bed to €0.50m).
4. **Coordinate audit.** Cross-checking each scheme's used coordinate against its own PPR
   sales and Mapbox forward-geocoding exposed several schemes that had drifted into the
   wrong district (three shared a single geocoder-fallback point). All are corrected via
   overrides below.

## By region

| Region | Developments | Units | Estimated value | Avg/unit |
|--------|-------------|-------|-----------------|----------|
| City Centre | 7 | 474 | €219,438,552 | €462,951 |
| South Dublin | 12 | 1,086 | €498,286,305 | €458,827 |
| North Dublin | 9 | 841 | €343,682,589 | €408,659 |
| West Dublin | 4 | 805 | €308,368,924 | €383,067 |
| West City | 3 | 409 | €153,087,309 | €374,297 |
| **Total** | **35** | **3,615** | **€1,522,863,679** | **€421,262** |

## By development

Per-unit = value ÷ IRES-owned units for that scheme. Type = the property type the model
matched comparables against. Geocode shows how the valuation coordinate was resolved
(`override` = curated/confirmed coordinate; see limitations).

| Development | Region | Type | Units | Est. value | Avg/unit | Geocode | Conf. |
|-------------|--------|------|-------|-----------|----------|---------|-------|
| The Marker | City Centre | apartment | 85 | €38,788,135 | €456,331 | database_exact | high |
| Xavier Court | City Centre | apartment | 41 | €12,046,112 | €293,808 | database_exact | high |
| Richmond Gardens | City Centre | apartment | 99 | €49,844,180 | €503,477 | override | high |
| Bakers Yard | City Centre | apartment | 81 | €47,522,501 | €586,698 | database_exact | high |
| Kings Court | City Centre | apartment | 83 | €31,738,560 | €382,392 | override | high |
| City Square | City Centre | apartment | 24 | €10,080,429 | €420,018 | database_exact | high |
| The School Yard | City Centre | apartment | 61 | €29,418,635 | €482,273 | database_exact | high |
| Rockbrook South Central | South Dublin | apartment | 189 | €77,177,799 | €408,348 | override | high |
| Tara View | South Dublin | apartment | 64 | €35,120,027 | €548,750 | database_exact | medium |
| The Maple | South Dublin | apartment | 68 | €31,253,691 | €459,613 | database_exact | high |
| The Forum | South Dublin | apartment | 7 | €3,422,363 | €488,909 | database_exact | high |
| Rockbrook Grande Central | South Dublin | apartment | 81 | €32,637,879 | €402,937 | override | high |
| Grande Central | South Dublin | apartment | 65 | €28,334,959 | €435,922 | override | high |
| Elmpark Green | South Dublin | apartment | 194 | €96,050,054 | €495,103 | database_exact | medium |
| Beacon South Quarter | South Dublin | apartment | 213 | €95,928,587 | €450,369 | database_exact | high |
| Bessboro | South Dublin | apartment | 40 | €19,439,000 | €485,975 | database_exact | medium |
| Belville Court | South Dublin | apartment | 19 | €8,532,971 | €449,104 | database_exact | high |
| Beechwood Court | South Dublin | apartment | 79 | €46,586,646 | €589,704 | eircode_routing_key | medium |
| Time Place | South Dublin | apartment | 67 | €23,802,329 | €355,259 | override | high |
| The Coast | North Dublin | apartment | 34 | €14,553,901 | €428,056 | database_exact | medium |
| Carrington Park | North Dublin | apartment | 142 | €58,591,067 | €412,613 | override | high |
| Taylor Hill | North Dublin | house | 78 | €26,514,900 | €339,935 | eircode_routing_key | high |
| Northern Cross | North Dublin | apartment | 115 | €56,601,523 | €492,187 | override | high |
| Heywood Court | North Dublin | apartment | 39 | €14,696,716 | €376,839 | override | high |
| Charlestown | North Dublin | apartment | 237 | €75,594,507 | €318,964 | database_exact | high |
| Ashbrook | North Dublin | apartment | 108 | €48,519,792 | €449,257 | eircode_routing_key | high |
| Waterside | North Dublin | apartment | 55 | €29,659,094 | €539,256 | eircode_routing_key | high |
| Semple Woods | North Dublin | house | 33 | €18,951,089 | €574,275 | eircode_routing_key | high |
| Coldcut Park | West Dublin | apartment | 91 | €43,553,674 | €478,612 | override | high |
| Tallaght Cross West | West Dublin | apartment | 460 | €143,193,981 | €311,291 | database_exact | high |
| Priorsgate | West Dublin | apartment | 108 | €48,281,748 | €447,053 | database_exact | high |
| Phoenix Park Racecourse | West Dublin | apartment | 146 | €73,339,521 | €502,325 | override | high |
| Lansdowne Gate | West City | apartment | 224 | €85,553,722 | €381,936 | database_exact | high |
| Tyrone Court | West City | apartment | 95 | €38,897,990 | €409,453 | eircode_routing_key | medium |
| Camac Crescent | West City | apartment | 90 | €28,635,597 | €318,173 | database_exact | high |

## By bedroom type (aggregate)

| Bedroom type | Units | Est. value | Avg/unit |
|--------------|-------|-----------|----------|
| studio | 7 | €2,922,927 | €417,561 |
| 1-bed | 792 | €268,927,929 | €339,555 |
| 2-bed | 2,280 | €976,023,914 | €428,081 |
| 2-bed duplex | 18 | €9,333,334 | €518,519 |
| 3-bed | 461 | €233,028,839 | €505,486 |
| 3-bed duplex | 15 | €9,385,320 | €625,688 |
| 4-bed | 42 | €23,241,416 | €553,367 |
| **Total** | **3,615** | **€1,522,863,679** | **€421,262** |

> The per-bedroom averages now rank as they should — 1-bed €340k < 2-bed €428k < 3-bed
> €505k < 4-bed €553k — because the bedroom ladder enforces that ordering everywhere.
> Duplex averages sit above their same-bedroom flats, as expected.

## Methodology & limitations (important)

1. **Apartment vs house are separate markets, and the model now enforces it three ways.**
   Same-type comparables are weighted 3×, opposite-type 0.05× (near-exclusion), unknown-type
   0.35×. Because ~69% of PPR rows carry **no** property_type, the type factor alone can't
   suppress unlabelled houses in house-heavy areas — so the **apartment-price ceiling**
   (built from *confirmed* local apartment sales) additionally drops any comparable priced
   like a house. This removed the residual seven-figure apartment overstatements seen in the
   earlier run (Richmond Gardens, Elmpark Green, Tara View, Phoenix Park are all now in a
   credible €0.50–0.55m/unit range).

2. **Coordinate corrections.** A coordinate audit (own-sales centroid + Mapbox
   verification) found 9 schemes had drifted into the wrong district under the DB
   street/routing-key match — three of them onto shared geocoder-fallback points
   (`53.2114,-6.1171` and `53.3964,-6.1298`). These are now pinned via overrides:
   Kings Court (D7), the three Rockbrook/Grande Central schemes and Time Place (Sandyford,
   D18), Carrington Park and Heywood Court (Santry, D9), Coldcut Park (Clondalkin, D22) and
   Northern Cross (Malahide Rd, D17), alongside the pre-existing Richmond Gardens and
   Phoenix Park Racecourse overrides. Kings Court, the Rockbrook trio and Time Place use
   coordinates confirmed manually; the rest were corroborated by Mapbox forward-geocoding.

3. **Shared coordinates within adjacent complexes.** The three Rockbrook/Grande Central
   schemes share one Sandyford coordinate (same complex), so their per-unit estimates are
   identical by construction; the split between them is not independently derived.

4. **Geocoding of the remainder.** Schemes not overridden resolved to a specific street via
   exact/full-text PPR match (`database_exact`) or fell back to the **Eircode routing-key
   centroid** (postal-district level, coarser). Development *marketing names* (e.g. 'The
   Marker') are absent from PPR data, so matching is on the street address, not the scheme
   name.

5. **Resale-only, open-market.** Comparables exclude non-full-market-price and bulk/
   multi-unit rows. New-build first sales are not the basis; this is a second-hand-market
   mark. No block/portfolio discount, transaction costs, or rental-yield basis applied.

6. **Unit counts** follow `docs/ires_reit_portfolio.md` (3,615 from bedroom breakdowns vs
   3,611 headline; the +4 is the documented Belville Court source anomaly).
