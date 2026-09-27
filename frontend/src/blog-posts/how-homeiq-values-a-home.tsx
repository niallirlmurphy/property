import { Link } from "react-router-dom";

// ---------------------------------------------------------------------------
// "How HomeIQ values a home" — a plain-English tour of the valuation engine
// behind /valuation. Deliberately conceptual: it explains the *ideas* (PPR as a
// base, enriched type + bedroom data layered on top, comparable selection, the
// size relationships we enforce) without publishing the exact weights, ratios
// or thresholds the model uses.
// ---------------------------------------------------------------------------

const INK = "#374151";
const INK_MUTED = "#6b7280";
const BLUE = "#2a78d6";
const GRID = "#e5e7eb";
const SURFACE = "#fcfcfb";

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "1.875rem", fontWeight: 600, color: "#111827", marginTop: "3rem", marginBottom: "1rem" }}>
      {children}
    </h2>
  );
}

// A simple, number-free illustration that a larger home is worth more than a
// smaller one nearby — the relationship the engine enforces. Heights are
// illustrative only (no model figures revealed).
function SizeLadderChart() {
  const bars = [
    { label: "1-bed", h: 0.62 },
    { label: "2-bed", h: 0.80 },
    { label: "3-bed", h: 1.0 },
  ];
  const W = 640, H = 260, padL = 20, padR = 20, padT = 20, padB = 40;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const groupW = plotW / bars.length;
  const barW = groupW * 0.5;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label="Illustrative bar chart showing that in the same location a two-bed home is worth more than a one-bed, and a three-bed more than a two-bed."
           style={{ background: SURFACE, borderRadius: "0.5rem", border: `1px solid ${GRID}` }}>
        {bars.map((b, i) => {
          const cx = padL + i * groupW + groupW / 2;
          const barH = b.h * plotH;
          const top = padT + plotH - barH;
          return (
            <g key={b.label}>
              <rect x={cx - barW / 2} y={top} width={barW} height={barH} rx={5} fill={BLUE} opacity={0.85}>
                <title>{`${b.label}: larger homes command more`}</title>
              </rect>
              <text x={cx} y={H - padB + 22} textAnchor="middle" fontSize={13} fontWeight={600} fill={INK}>{b.label}</text>
            </g>
          );
        })}
        <text x={padL} y={padT - 4} fontSize={11} fill={INK_MUTED}>value in the same location →</text>
      </svg>
      <figcaption style={{ fontSize: "0.9rem", color: INK_MUTED, marginTop: "0.5rem" }}>
        Illustrative only. In a given location a two-bed sells for more than a one-bed, and a three-bed for more than a
        two-bed. The engine measures these relationships from thousands of real sales and holds to them, so a larger home
        is never valued below a smaller one next door.
      </figcaption>
    </figure>
  );
}

export function HowHomeIqValuesContent() {
  return (
    <div style={{ fontSize: "1.125rem", lineHeight: 1.75, color: INK }}>
      <p style={{ marginBottom: "1.5rem" }}>
        Every property valuation is really an answer to one hard question: <em>what would this specific home sell for
        today?</em> Our{" "}
        <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>instant valuation tool</Link> answers it for
        any Irish address in seconds, built entirely on real, public sold-price data. This post lifts the lid on how it
        works — not the secret sauce, but the ideas: where the data comes from, what we add to it, and the recent work
        that makes each estimate more trustworthy.
      </p>

      <SectionHeading>The foundation: the Property Price Register</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Ireland is fortunate to have the{" "}
        <Link to="/blog/how-to-use-property-price-register" style={{ color: "#1d4ed8", fontWeight: 600 }}>Property Price
        Register</Link> (PPR): a public record of <strong>every residential property sale since 2010</strong>, with the
        address, the date and the actual price paid. That is gold for valuation. It isn't a listing site's asking prices
        or an estate agent's guide — it's what buyers <em>actually paid</em>, which is the only number that really
        matters. Hundreds of thousands of these transactions are the bedrock of everything we do.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        But raw PPR data, on its own, only gets you so far. It tells you an address and a price — and little else. It
        doesn't tell you whether a sale was a one-bed apartment or a five-bed house. It has no coordinates, so you can't
        easily ask "what sold <em>near here?</em>". Addresses are written inconsistently, with abbreviations, punctuation
        and typos. And a headline figure from a single nearby sale can be wildly misleading. Turning that raw register
        into a reliable per-home estimate is the real work.
      </p>

      <SectionHeading>What we layer on top</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        We treat the PPR as a base and enrich it into something far more useful:
      </p>
      <ul style={{ marginBottom: "1rem", paddingLeft: "1.25rem" }}>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Precise geography.</strong> Every sale is geocoded to a map coordinate, so we can find genuinely nearby
          comparables rather than relying on a town or postcode label.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Clean, consistent addresses.</strong> We normalise every address to a standard form — expanding
          abbreviations, fixing punctuation and spacing — so "28 Slane Rd" and "28 Slane Road" are recognised as the same
          place.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Property type.</strong> The PPR doesn't say whether a sale is a house or an apartment. We enrich sales
          with that classification, because — as we'll see — it changes everything.
        </li>
        <li style={{ marginBottom: "0.6rem" }}>
          <strong>Bedroom counts.</strong> We add bedroom information where we can, so a valuation can lean on homes of a
          genuinely similar size, not just a similar location.
        </li>
      </ul>
      <p style={{ marginBottom: "1rem" }}>
        This enriched layer is what separates a useful estimate from a crude "average price in the area" figure. It's the
        difference between "homes around here sold for about X" and "a home <em>like yours</em> is worth about X."
      </p>

      <SectionHeading>Finding the right comparables</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        With that foundation in place, valuing a home follows the same logic a good estate agent would use — just at
        scale, and consistently. We gather recent, arm's-length sales near the property, widening the search until we have
        enough to be meaningful, and we bring every one of them to <strong>today's money</strong> using local price
        trends, so a 2023 sale is expressed in 2026 terms. Closer, more recent and more <em>similar</em> sales count for
        more.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        The word doing the heavy lifting there is <em>similar</em>. One of the most important refinements we've made is to
        treat <strong>apartments and houses as separate markets</strong>. Valuing a two-bed apartment off the three-bed
        semis on the next street gives a badly inflated number — they simply aren't the same product. So the engine leans
        overwhelmingly on same-type sales and all but ignores the other type. Getting property type right is often the
        single biggest factor in a sensible apartment valuation.
      </p>

      <SectionHeading>Recent work: outliers and the size relationship</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        Two pieces of recent analysis have made our estimates noticeably more robust.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Setting aside local outliers.</strong> Occasionally a single unusual sale — a penthouse, a large
        multi-unit deal, a trophy home — lands right beside a cluster of ordinary sales. Left unchecked, one such price
        can hijack the whole estimate. We now detect when a nearby sale is a statistical outlier relative to its
        neighbours and stop it from dominating, so your valuation reflects the ordinary market around you, not the one
        exceptional deal.
      </p>
      <p style={{ marginBottom: "1rem" }}>
        <strong>Respecting how size drives price.</strong> Analysing thousands of sales confirms an intuitive truth: in
        the same location, a two-bed is worth more than a one-bed, and a three-bed more than a two-bed. That sounds
        obvious, but a naïve model that just averages nearby prices can break it — especially where there are only a
        handful of sales of a given size. We measure these size relationships directly from the data and build them into
        the engine, so a larger home is never valued below a smaller one next door, and a size with thin local data still
        gets a sensible, properly-ranked figure.
      </p>
      <SizeLadderChart />

      <SectionHeading>Honest by design</SectionHeading>
      <p style={{ marginBottom: "1rem" }}>
        No statistical model is a substitute for a valuer standing in the room, and we don't pretend otherwise. That's why
        every estimate on HomeIQ comes with its working shown: the <strong>comparable sales</strong> we used, how far away
        and how recent they were, and a <strong>confidence level</strong> that reflects how much good data stood behind
        the number. A tight cluster of recent, same-type, same-size sales next door earns high confidence; a sparse,
        scattered pool earns a wider range and a note of caution. You get a number <em>and</em> the reasons for it.
      </p>

      <SectionHeading>Try it on your own home</SectionHeading>
      <p style={{ marginBottom: "2rem" }}>
        The same engine that we've pointed at entire portfolios runs when you type in a single address. It starts from
        real sold prices, enriches them with location, type and size, chooses the right comparables, and shows you exactly
        what's behind the result. It's free, instant, and built on data you can check yourself.
      </p>

      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "0.5rem", padding: "1.5rem", marginTop: "2rem" }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Curious what your home is worth?</strong> Get a free instant valuation built from real comparable sales
          near you — with the comparables and confidence shown, and apartments valued off apartments.{" "}
          <Link to="/valuation" style={{ color: "#1d4ed8", fontWeight: 600 }}>Value your property →</Link>
        </p>
      </div>

      <p style={{ fontSize: "0.82rem", color: INK_MUTED, marginTop: "2.5rem", fontStyle: "italic" }}>
        HomeIQ valuations are an indicative statistical model based on Property Price Register data and are not a valuation
        of record, investment advice, or a recommendation. For a formal valuation, consult a qualified valuer.
      </p>
    </div>
  );
}
