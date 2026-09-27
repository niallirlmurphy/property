# IRES REIT — Portfolio Valuation (IRES-owned units)

**Method:** HomeIQ valuation pipeline (`POST /valuation/estimate` internals) run per
development × bedroom type, driven by an explicit coordinate per development.
**Comparables:** PPR resale sales within an adaptive 1–20 km radius, last 3 years,
time-adjusted to today via county price indices, weighted by distance + recency +
bedroom match + **property-type match** (apartment vs house). Bulk/multi-unit rows and
out-of-band prices are excluded.
**Valued:** 2026-09-27 · **Source portfolio:** `docs/ires_reit_portfolio.md`
**Raw output:** `docs/ires_valuation_raw.json`

## Headline

| | |
|---|---|
| Developments | 35 |
| IRES-owned units valued | 3,615 |
| **Estimated gross value** | **€2,004,781,576** (≈ €2.00 bn) |
| Rows valued | 106 / 106 bedroom-type rows |

> ⚠️ **Read this as an indicative model estimate, not a valuation of record.** It is
> built from open-market PPR *resale* comparables, so it reflects what comparable
> second-hand homes near each scheme have sold for — not IRES's book value, not a
> block/portfolio (bulk-discounted) value, and not rental/investment (yield) value. A
> real institutional block would typically transact **below** the sum-of-units figure.
> Several caveats below materially affect individual developments.

### Change from the type-blind run

This valuation now **weights comparables heavily toward matching property type**
(apartment vs house are treated as separate markets). Versus the earlier type-blind run
(€2,104,515,690), the total fell ~€100m. Apartment schemes previously pulled up by nearby
house sales came down — e.g. The Marker €555k → €461k/unit, Elmpark Green €1.26m →
€1.09m/unit, Tara View €1.26m → €1.10m/unit — while house schemes (Taylor Hill, Semple
Woods) are now valued against houses only.

## By region

| Region | Developments | Units | Estimated value |
|--------|-------------|-------|-----------------|
| City Centre | 7 | 474 | €348,225,195 |
| South Dublin | 12 | 1,086 | €757,366,803 |
| North Dublin | 9 | 841 | €393,457,990 |
| West Dublin | 4 | 805 | €354,722,738 |
| West City | 3 | 409 | €151,008,850 |
| **Total** | **35** | **3,615** | **€2,004,781,576** |

## By development

Per-unit = simple average of the bedroom-type estimates for that scheme. Type = the
property type the model matched comparables against. Geocode shows how the valuation
coordinate was resolved. ⚠ = shares its coordinate (and therefore its per-unit estimates)
with another scheme — see limitations.

| Development | Region | Type | Units | Est. value | Avg/unit | Geocode | Conf. |
|-------------|--------|------|-------|-----------|----------|---------|-------|
| The Marker | City Centre | apartment | 85 | €39,174,120 | €460,872 | database_exact | high |
| Xavier Court | City Centre | apartment | 41 | €12,768,798 | €309,633 | database_exact | medium |
| Richmond Gardens | City Centre | apartment | 99 | €143,181,728 | €1,484,962 | override | medium |
| Bakers Yard | City Centre | apartment | 81 | €65,630,493 | €824,581 | database_exact | medium |
| Kings Court | City Centre | apartment | 83 | €44,547,315 | €538,070 | database_exact | high |
| City Square | City Centre | apartment | 24 | €11,786,142 | €492,825 | database_exact | high |
| The School Yard | City Centre | apartment | 61 | €31,136,599 | €498,177 | database_exact | medium |
| Rockbrook South Central ⚠ | South Dublin | apartment | 189 | €121,852,383 | €674,037 | database_exact | medium |
| Tara View ⚠ | South Dublin | apartment | 64 | €69,956,715 | €1,103,554 | database_exact | medium |
| The Maple ⚠ | South Dublin | apartment | 68 | €33,670,163 | €498,088 | database_exact | high |
| The Forum | South Dublin | apartment | 7 | €3,467,655 | €493,145 | database_exact | high |
| Rockbrook Grande Central ⚠ | South Dublin | apartment | 81 | €51,770,893 | €674,037 | database_exact | medium |
| Grande Central ⚠ | South Dublin | apartment | 65 | €43,007,117 | €674,037 | database_exact | medium |
| Elmpark Green ⚠ | South Dublin | apartment | 194 | €216,935,936 | €1,093,346 | database_exact | medium |
| Beacon South Quarter ⚠ | South Dublin | apartment | 213 | €103,588,046 | €498,087 | database_exact | high |
| Bessboro | South Dublin | apartment | 40 | €19,666,414 | €534,632 | database_exact | medium |
| Belville Court | South Dublin | apartment | 19 | €8,389,495 | €441,370 | database_exact | high |
| Beechwood Court | South Dublin | apartment | 79 | €46,754,622 | €591,839 | eircode_routing_key | medium |
| Time Place | South Dublin | apartment | 67 | €38,307,364 | €579,191 | database_exact | high |
| The Coast | North Dublin | apartment | 34 | €17,657,481 | €515,260 | database_exact | medium |
| Carrington Park ⚠ | North Dublin | apartment | 142 | €60,909,938 | €430,804 | database_exact | high |
| Taylor Hill | North Dublin | house | 78 | €26,707,632 | €343,104 | eircode_routing_key | high |
| Northern Cross | North Dublin | apartment | 115 | €78,902,981 | €686,479 | database_exact | medium |
| Heywood Court ⚠ | North Dublin | apartment | 39 | €16,683,854 | €431,221 | database_exact | high |
| Charlestown | North Dublin | apartment | 237 | €84,325,996 | €368,244 | database_exact | high |
| Ashbrook | North Dublin | apartment | 108 | €49,065,237 | €463,587 | eircode_routing_key | medium |
| Waterside ⚠ | North Dublin | apartment | 55 | €36,241,910 | €665,208 | eircode_routing_key | medium |
| Semple Woods ⚠ | North Dublin | house | 33 | €22,962,961 | €712,188 | eircode_routing_key | medium |
| Coldcut Park | West Dublin | apartment | 91 | €50,568,168 | €551,410 | database_exact | medium |
| Tallaght Cross West | West Dublin | apartment | 460 | €144,821,159 | €314,070 | database_exact | high |
| Priorsgate | West Dublin | apartment | 108 | €39,255,452 | €375,892 | database_exact | high |
| Phoenix Park Racecourse | West Dublin | apartment | 146 | €120,077,959 | €806,739 | database_exact | medium |
| Lansdowne Gate | West City | apartment | 224 | €80,347,895 | €357,633 | database_exact | high |
| Tyrone Court | West City | apartment | 95 | €37,390,793 | €395,522 | eircode_routing_key | medium |
| Camac Crescent | West City | apartment | 90 | €33,270,162 | €366,529 | database_exact | medium |

## By bedroom type (aggregate)

| Bedroom type | Units | Est. value | Avg/unit |
|--------------|-------|-----------|----------|
| studio | 7 | €4,733,101 | €818,270 |
| 1-bed | 792 | €447,808,822 | €566,913 |
| 2-bed | 2,280 | €1,240,313,810 | €563,775 |
| 2-bed duplex | 18 | €14,519,542 | €771,492 |
| 3-bed | 461 | €263,256,360 | €623,861 |
| 3-bed duplex | 15 | €10,774,335 | €718,289 |
| 4-bed | 42 | €23,375,606 | €509,845 |
| **Total** | **3,615** | **€2,004,781,576** | **€554,435** |

> The 1-bed and 2-bed per-unit averages are now close (€567k vs €564k), as you'd expect
> for a market where a 1-bed and a small 2-bed in the same block sell for similar money.
> Studio and duplex averages sit high because those tiny counts fall almost entirely in
> pricey schemes.

## Methodology & limitations (important)

1. **Property-type matching is now applied, but is only as good as the type labels.**
   The model weights same-type comparables (apartment↔apartment) at 3× and opposite-type
   (a house when valuing an apartment) at 0.05× — near-exclusion. However ~69% of PPR rows
   carry **no** property_type; those "unknown" comparables sit at 0.35×, so in areas where
   expensive *houses* dominate the unlabelled pool, apartment schemes are still pulled up.
   Clearest residual overstatements:
   - **Richmond Gardens** (D3, on the authoritative override coordinate): ~€1.48m/unit —
     implausible for these apartments; the local labelled-apartment pool is thin, so a few
     high sales dominate. Treat as an upper bound / outlier.
   - **Elmpark Green / Tara View** (Merrion Road, D4): ~€1.09–1.10m/unit — down from ~€1.26m
     under the type-blind run, but D4 is expensive across all stock.
   - **Phoenix Park Racecourse** (Castleknock, D15): ~€0.81m/unit.
   These few schemes skew the €2.00 bn headline high; the true figures are lower.

2. **Coordinate collisions — 5 groups share one valuation point** (same street or Eircode
   routing key), so each group's schemes get identical per-unit estimates:
   - Grande Central, Rockbrook Grande Central, Rockbrook South Central (all €674,037/unit)
   - Elmpark Green, Tara View
   - Beacon South Quarter, The Maple (both €498k/unit)
   - Carrington Park, Heywood Court
   - Semple Woods, Waterside
   These are adjacent/same-complex schemes, so shared pricing is defensible, but the
   per-development split within a group is not independently derived.

3. **Geocoding.** 26 developments resolved to a specific street via exact/full-text PPR
   match (`database_exact`); the rest fell back to the **Eircode routing-key centroid**
   (postal-district level, coarser) or, for Richmond Gardens, a **curated override**
   coordinate supplied for this exercise. Development *marketing names* (e.g. 'The Marker')
   are absent from PPR data, so matching is on the street address, not the scheme name.
   The 30 km routing-key guard correctly rejected one wrong-area match (Taylor Hill).

4. **Resale-only, open-market.** Comparables exclude non-full-market-price and bulk/
   multi-unit rows. New-build first sales are not the basis; this is a second-hand-market
   mark. No block/portfolio discount, transaction costs, or rental-yield basis applied.

5. **Unit counts** follow `docs/ires_reit_portfolio.md` (3,615 from bedroom breakdowns vs
   3,611 headline; the +4 is the documented Belville Court source anomaly).
