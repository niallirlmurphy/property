export default function Footer() {
  return (
    <div className="site-footer">
      <p>
        <a href="/">Standard Search</a>
        <span className="separator">•</span>
        <a href="/valuation">Property Valuation</a>
        <span className="separator">•</span>
        <a href="/s1">Single Property Search</a>
        <span className="separator">•</span>
        <a href="/polygon">Map Search</a>
        <span className="separator">•</span>
        <a href="/about">About</a>
      </p>
      <p className="build-info">
        Build: {new Date().toLocaleString("en-IE", {
          dateStyle: "medium",
          timeStyle: "short",
        })}
      </p>
    </div>
  );
}
