import { useParams, Link, Navigate } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import WaffleMenu from "../components/WaffleMenu";
import Footer from "../components/Footer";
import { BLOG_POSTS } from "./BlogListPage";

// Blog post content - import from individual files
import { HowToUsePPRContent } from "../blog-posts/how-to-use-property-price-register";
import { DublinPostcodesContent } from "../blog-posts/dublin-property-prices-by-postcode-2026";
import { EircodeGuideContent } from "../blog-posts/understanding-eircode-property-search";
import { IrelandsLongestGreenwayContent } from "../blog-posts/irelands-longest-greenway";

// Map slugs to content components
const BLOG_CONTENT: Record<string, React.ComponentType> = {
  "irelands-longest-greenway": IrelandsLongestGreenwayContent,
  "how-to-use-property-price-register": HowToUsePPRContent,
  "dublin-property-prices-by-postcode-2026": DublinPostcodesContent,
  "understanding-eircode-property-search": EircodeGuideContent,
};

export default function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>();

  if (!slug) {
    return <Navigate to="/blog" replace />;
  }

  // Find post metadata
  const post = BLOG_POSTS.find((p) => p.slug === slug);
  const ContentComponent = BLOG_CONTENT[slug];

  // 404 if post not found
  if (!post || !ContentComponent) {
    return <Navigate to="/blog" replace />;
  }

  // Set SEO meta tags
  usePageMeta(
    post.title,
    post.description,
    [{ name: "Blog", url: "/blog" }]
  );

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f8f9fa" }}>
      <WaffleMenu />

      {/* Header */}
      <header style={{
        backgroundColor: "#fff",
        borderBottom: "1px solid #e5e7eb",
        padding: "2rem 1rem 3rem"
      }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <Link to="/blog" style={{
            color: "#6b7280",
            textDecoration: "none",
            fontSize: "0.875rem",
            marginBottom: "1rem",
            display: "inline-block"
          }}>
            ← Back to Blog
          </Link>

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
          <h1 style={{
            fontSize: "2.5rem",
            fontWeight: "bold",
            color: "#111827",
            marginBottom: "1rem",
            lineHeight: "1.2"
          }}>
            {post.title}
          </h1>

          {/* Meta info */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            fontSize: "0.875rem",
            color: "#9ca3af"
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
        </div>
      </header>

      {/* Article content */}
      <article style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "2rem 1rem",
        backgroundColor: "#fff",
        minHeight: "60vh"
      }}>
        <div className="blog-content">
          <ContentComponent />
        </div>
      </article>

      {/* Footer CTA */}
      <div style={{
        maxWidth: "800px",
        margin: "2rem auto",
        padding: "0 1rem"
      }}>
        <div style={{
          backgroundColor: "#eff6ff",
          border: "1px solid #bfdbfe",
          borderRadius: "0.5rem",
          padding: "2rem",
          textAlign: "center"
        }}>
          <h3 style={{
            fontSize: "1.25rem",
            fontWeight: "600",
            color: "#111827",
            marginBottom: "0.5rem"
          }}>
            Ready to search property prices?
          </h3>
          <p style={{
            color: "#6b7280",
            marginBottom: "1.5rem"
          }}>
            Search 785,000 Irish property sales with interactive maps and price trends.
          </p>
          <Link
            to="/"
            style={{
              display: "inline-block",
              backgroundColor: "#3b82f6",
              color: "#fff",
              padding: "0.75rem 1.5rem",
              borderRadius: "0.375rem",
              textDecoration: "none",
              fontWeight: "500"
            }}
          >
            Start Searching
          </Link>
        </div>

        {/* Back to blog */}
        <div style={{
          marginTop: "2rem",
          textAlign: "center"
        }}>
          <Link
            to="/blog"
            style={{
              color: "#6b7280",
              textDecoration: "none",
              fontSize: "0.875rem"
            }}
          >
            ← Back to all articles
          </Link>
        </div>
      </div>
      <Footer />
    </div>
  );
}
