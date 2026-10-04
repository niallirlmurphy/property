import { Link } from "react-router-dom";
import { Head } from "vite-react-ssg";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";

// Catch-all route. Prerendered as /404 and copied to dist/404.html, which Vercel
// serves with a real 404 status for any URL with no static file — so unknown
// URLs are no longer 200 soft-404s canonicalised to the homepage.
export default function NotFoundPage() {
  return (
    <>
      <Head>
        <title>Page not found | HomeIQ</title>
        <meta name="robots" content="noindex" />
      </Head>
      <PageHeader title="Page not found" titleAsHeading={false} />
      <div className="content-page">
        <h1>Page not found</h1>
        <p>We couldn't find that page. It may have moved, or the address may be mistyped.</p>
        <ul>
          <li><Link to="/">Search property prices</Link></li>
          <li><Link to="/areaguides">Browse area guides</Link></li>
          <li><Link to="/streets">Browse streets</Link></li>
          <li><Link to="/blog">Read the blog</Link></li>
        </ul>
      </div>
      <Footer />
    </>
  );
}
