import { Link } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import WaffleMenu from "../components/WaffleMenu";
import Footer from "../components/Footer";

// Blog post metadata
export interface BlogPost {
  slug: string;
  title: string;
  description: string;
  date: string;
  author: string;
  tags: string[];
  readTime: string;
}

// Blog posts index - add new posts here
export const BLOG_POSTS: BlogPost[] = [
  {
    slug: "best-month-to-sell-property-ireland",
    title: "Which Month Is the Best Month to Sell Your Property in Ireland?",
    description: "We analysed 749,031 property sales since 2010 to find the best time to sell a home in Ireland. Autumn brings the highest prices and the busiest market — here's the data.",
    date: "2026-07-18",
    author: "HomeIQ Team",
    tags: ["Analysis", "Selling", "Market Trends", "Seasonality"],
    readTime: "10 min read"
  },
  {
    slug: "irelands-longest-greenway",
    title: "Ireland's Longest Greenway",
    description: "Guide to Ireland's Longest Greenway - the 125km Royal Canal Greenway and Old Rail Trail route from Leixlip to Athlone.",
    date: "2026-06-22",
    author: "HomeIQ Team",
    tags: ["Greenway", "Midlands", "Amenities", "Cycling"],
    readTime: "5 min read"
  },
  {
    slug: "how-to-use-property-price-register",
    title: "How to Use Ireland's Property Price Register - Complete Guide",
    description: "Learn how to search and interpret data from Ireland's Property Price Register, including tips for finding accurate property sale prices.",
    date: "2026-06-08",
    author: "HomeIQ Team",
    tags: ["Guide", "PPR", "Property Search"],
    readTime: "8 min read"
  },
  {
    slug: "dublin-property-prices-by-postcode-2026",
    title: "Dublin Property Prices by Postcode - 2026 Guide",
    description: "Complete breakdown of property prices across all Dublin postcodes, from D01 to D22 and D6W. Find the most and least expensive areas.",
    date: "2026-06-08",
    author: "HomeIQ Team",
    tags: ["Dublin", "Analysis", "Postcodes"],
    readTime: "10 min read"
  },
  {
    slug: "understanding-eircode-property-search",
    title: "Understanding Eircode for Property Search",
    description: "What are Eircodes? How do routing keys work? Learn how to use Eircode data to search for property prices in your area.",
    date: "2026-06-08",
    author: "HomeIQ Team",
    tags: ["Guide", "Eircode", "Tutorial"],
    readTime: "6 min read"
  },
];

export default function BlogListPage() {
  usePageMeta(
    "Property Price Blog - Guides & Market Analysis",
    "Expert guides, market analysis, and insights on Irish property prices. Learn how to search property data, understand market trends, and make informed decisions."
  );

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f8f9fa" }}>
      <WaffleMenu />

      {/* Header */}
      <header style={{
        backgroundColor: "#fff",
        borderBottom: "1px solid #e5e7eb",
        padding: "2rem 1rem"
      }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <Link to="/" style={{
            color: "#6b7280",
            textDecoration: "none",
            fontSize: "0.875rem",
            marginBottom: "0.5rem",
            display: "inline-block"
          }}>
            ← Back to Home
          </Link>
          <h1 style={{
            fontSize: "2.5rem",
            fontWeight: "bold",
            color: "#111827",
            marginBottom: "0.5rem"
          }}>
            Property Price Blog
          </h1>
          <p style={{
            fontSize: "1.125rem",
            color: "#6b7280",
            lineHeight: "1.75"
          }}>
            Guides, market analysis, and insights on Irish property prices
          </p>
        </div>
      </header>

      {/* Blog posts list */}
      <main style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "2rem 1rem"
      }}>
        <div style={{
          display: "grid",
          gap: "2rem"
        }}>
          {BLOG_POSTS.map((post) => (
            <article
              key={post.slug}
              style={{
                backgroundColor: "#fff",
                borderRadius: "0.5rem",
                padding: "2rem",
                boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.1)",
                transition: "box-shadow 0.2s",
                border: "1px solid #e5e7eb"
              }}
            >
              {/* Tags */}
              <div style={{
                display: "flex",
                gap: "0.5rem",
                marginBottom: "1rem",
                flexWrap: "wrap"
              }}>
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: "500",
                      color: "#3b82f6",
                      backgroundColor: "#eff6ff",
                      padding: "0.25rem 0.75rem",
                      borderRadius: "9999px"
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Title */}
              <Link
                to={`/blog/${post.slug}`}
                style={{
                  textDecoration: "none",
                  color: "#111827"
                }}
              >
                <h2 style={{
                  fontSize: "1.5rem",
                  fontWeight: "600",
                  marginBottom: "0.75rem",
                  lineHeight: "1.4"
                }}>
                  {post.title}
                </h2>
              </Link>

              {/* Description */}
              <p style={{
                color: "#6b7280",
                lineHeight: "1.75",
                marginBottom: "1rem"
              }}>
                {post.description}
              </p>

              {/* Meta info */}
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "1rem",
                fontSize: "0.875rem",
                color: "#9ca3af",
                marginBottom: "1rem"
              }}>
                <span>{post.author}</span>
                <span>•</span>
                <time>{new Date(post.date).toLocaleDateString("en-IE", {
                  year: "numeric",
                  month: "long",
                  day: "numeric"
                })}</time>
                <span>•</span>
                <span>{post.readTime}</span>
              </div>

              {/* Read more link */}
              <Link
                to={`/blog/${post.slug}`}
                style={{
                  color: "#3b82f6",
                  fontWeight: "500",
                  textDecoration: "none",
                  fontSize: "0.875rem"
                }}
              >
                Read article →
              </Link>
            </article>
          ))}
        </div>

        {/* Coming soon message */}
        <div style={{
          marginTop: "3rem",
          padding: "2rem",
          backgroundColor: "#fff",
          borderRadius: "0.5rem",
          border: "1px solid #e5e7eb",
          textAlign: "center"
        }}>
          <p style={{ color: "#6b7280", marginBottom: "0.5rem" }}>
            More articles coming soon!
          </p>
          <p style={{ fontSize: "0.875rem", color: "#9ca3af" }}>
            We publish new property market insights every week.
          </p>
        </div>
      </main>
      <Footer />
    </div>
  );
}
