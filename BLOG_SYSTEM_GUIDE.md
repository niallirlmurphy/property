# Blog System Guide

**Created:** 2026-06-08  
**Status:** ✅ Live and ready to use

---

## 📁 Files Created

### Pages
- `frontend/src/pages/BlogListPage.tsx` - Blog listing page (`/blog`)
- `frontend/src/pages/BlogPostPage.tsx` - Individual blog post template (`/blog/:slug`)

### Blog Post Content
- `frontend/src/blog-posts/how-to-use-property-price-register.tsx` - ✅ Complete
- `frontend/src/blog-posts/dublin-property-prices-by-postcode-2026.tsx` - 🟡 Placeholder
- `frontend/src/blog-posts/understanding-eircode-property-search.tsx` - 🟡 Placeholder

### Routing
- Updated `frontend/src/main.tsx` with blog routes

---

## 🎯 How to Add a New Blog Post

### Step 1: Add Metadata to Blog Index

Edit `frontend/src/pages/BlogListPage.tsx` and add to the `BLOG_POSTS` array:

```tsx
{
  slug: "your-post-slug",
  title: "Your Post Title",
  description: "SEO-friendly description (150-160 chars)",
  date: "2026-06-15",
  author: "HomeIQ Team",
  tags: ["Guide", "Analysis", "Dublin"],  // 2-4 tags
  readTime: "7 min read"
}
```

### Step 2: Create Content File

Create `frontend/src/blog-posts/your-post-slug.tsx`:

```tsx
import { Link } from "react-router-dom";

export function YourPostSlugContent() {
  return (
    <div style={{
      fontSize: "1.125rem",
      lineHeight: "1.75",
      color: "#374151"
    }}>
      {/* Introduction */}
      <p style={{ marginBottom: "2rem" }}>
        Your intro paragraph goes here...
      </p>

      {/* Section */}
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "3rem",
        marginBottom: "1rem"
      }}>
        Section Heading
      </h2>

      <p style={{ marginBottom: "2rem" }}>
        Section content...
      </p>

      {/* Subsection */}
      <h3 style={{
        fontSize: "1.5rem",
        fontWeight: "600",
        color: "#111827",
        marginTop: "2rem",
        marginBottom: "1rem"
      }}>
        Subsection Heading
      </h3>

      <p style={{ marginBottom: "1rem" }}>
        Paragraph with a <Link to="/county/dublin" style={{ color: "#3b82f6" }}>link to county page</Link>.
      </p>

      {/* List */}
      <ul style={{
        marginBottom: "2rem",
        paddingLeft: "2rem",
        listStyle: "disc"
      }}>
        <li style={{ marginBottom: "0.5rem" }}>List item 1</li>
        <li style={{ marginBottom: "0.5rem" }}>List item 2</li>
        <li style={{ marginBottom: "0.5rem" }}>List item 3</li>
      </ul>

      {/* Callout box */}
      <div style={{
        backgroundColor: "#eff6ff",
        border: "1px solid #bfdbfe",
        borderRadius: "0.5rem",
        padding: "1.5rem",
        marginBottom: "2rem"
      }}>
        <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
          <strong>Tip:</strong> Important callout goes here.
        </p>
      </div>

      {/* More content... */}
    </div>
  );
}
```

### Step 3: Register Content Component

Edit `frontend/src/pages/BlogPostPage.tsx` and add your import and mapping:

```tsx
// Add import at top
import { YourPostSlugContent } from "../blog-posts/your-post-slug";

// Add to BLOG_CONTENT object
const BLOG_CONTENT: Record<string, React.ComponentType> = {
  "how-to-use-property-price-register": HowToUsePPRContent,
  "your-post-slug": YourPostSlugContent,  // Add this line
  // ...
};
```

### Step 4: Deploy

```bash
git add frontend/src/
git commit -m "blog: add [post title]"
git push origin main
```

Done! Your post is now live at `https://homeiq.ie/blog/your-post-slug`

---

## 🎨 Styling Components

### Headings

```tsx
{/* H2 - Main section */}
<h2 style={{
  fontSize: "1.875rem",
  fontWeight: "600",
  color: "#111827",
  marginTop: "3rem",
  marginBottom: "1rem"
}}>
  Section Title
</h2>

{/* H3 - Subsection */}
<h3 style={{
  fontSize: "1.5rem",
  fontWeight: "600",
  color: "#111827",
  marginTop: "2rem",
  marginBottom: "1rem"
}}>
  Subsection Title
</h3>
```

### Paragraphs

```tsx
<p style={{ marginBottom: "2rem" }}>
  Regular paragraph with 2rem bottom margin.
</p>
```

### Lists

```tsx
{/* Unordered list */}
<ul style={{
  marginBottom: "2rem",
  paddingLeft: "2rem",
  listStyle: "disc"
}}>
  <li style={{ marginBottom: "0.5rem" }}>Item</li>
</ul>

{/* Ordered list */}
<ol style={{
  marginBottom: "2rem",
  paddingLeft: "2rem",
  listStyle: "decimal"
}}>
  <li style={{ marginBottom: "0.75rem" }}>
    <strong>Step 1:</strong> Description
  </li>
</ol>
```

### Callout Boxes

```tsx
{/* Blue info box */}
<div style={{
  backgroundColor: "#eff6ff",
  border: "1px solid #bfdbfe",
  borderRadius: "0.5rem",
  padding: "1.5rem",
  marginBottom: "2rem"
}}>
  <p style={{ fontSize: "1rem", color: "#1e40af", margin: 0 }}>
    <strong>Tip:</strong> Your tip here.
  </p>
</div>

{/* Yellow warning box */}
<div style={{
  backgroundColor: "#fef3c7",
  border: "1px solid #fbbf24",
  borderRadius: "0.5rem",
  padding: "1rem",
  marginBottom: "2rem"
}}>
  <p style={{ fontSize: "1rem", color: "#78350f", margin: 0 }}>
    <strong>Important:</strong> Warning message here.
  </p>
</div>

{/* Gray neutral box */}
<div style={{
  backgroundColor: "#f3f4f6",
  padding: "1rem",
  borderRadius: "0.375rem",
  marginBottom: "2rem"
}}>
  <p style={{ margin: 0 }}>Neutral callout content.</p>
</div>
```

### Links

```tsx
{/* Internal link */}
<Link to="/county/dublin" style={{ color: "#3b82f6" }}>
  Dublin county page
</Link>

{/* External link */}
<a 
  href="https://example.com" 
  target="_blank" 
  rel="noopener noreferrer" 
  style={{ color: "#3b82f6" }}
>
  External site
</a>
```

---

## 📝 Content Guidelines

### Title
- Keep under 60 characters
- Include primary keyword
- Be specific and actionable
- Examples:
  - ✅ "How to Use Ireland's Property Price Register - Complete Guide"
  - ❌ "PPR Guide" (too vague)

### Description
- 150-160 characters (for SEO)
- Include call-to-action or benefit
- Examples:
  - ✅ "Learn how to search and interpret data from Ireland's Property Price Register, including tips for finding accurate property sale prices."
  - ❌ "A guide about the PPR."

### Tags
- 2-4 tags per post
- Use consistent tags across posts
- Common tags:
  - Guide
  - Analysis
  - Tutorial
  - Market Report
  - County names (Dublin, Cork, etc.)
  - Features (Eircode, Maps, Trends)

### Read Time
- Count words, divide by 200 (average reading speed)
- Round to nearest minute
- Format: "7 min read"

### Content Length
- Minimum: 800 words
- Ideal: 1,500-2,500 words
- Long-form (3,000+): For comprehensive guides

### Structure
- **Introduction** (1-2 paragraphs) - Hook + value proposition
- **3-5 main sections** - Each with H2 heading
- **Subsections as needed** - H3 headings
- **Conclusion** - Summary + CTA

### Writing Style
- **Conversational but professional**
- Use short paragraphs (2-3 sentences)
- Bullet points for lists
- Bold important terms on first use
- Examples and real data
- Internal links to relevant pages

### SEO Optimization
- Include target keyword in:
  - Title
  - Description
  - First paragraph
  - At least one H2 heading
  - Naturally throughout content
- Link to 3-5 internal pages
- Use descriptive link text (not "click here")

---

## 🔗 Internal Linking Strategy

Link to these pages from blog posts:

### Main Pages
- `/` - Homepage (property search)
- `/about` - About page
- `/property-price-register` - PPR info page
- `/polygon` - Polygon search

### County Pages
- `/county/dublin`
- `/county/cork`
- `/county/galway`
- (all 26 counties)

### Area Pages
- `/area/ballsbridge`
- `/area/sandymount`
- (50+ areas)

### Eircode Pages
- `/eircode/D02`
- `/eircode/H91`
- (301 routing keys)

### Other Blog Posts
- `/blog/how-to-use-property-price-register`
- (link related posts)

**Rule:** Every blog post should link to at least 3-5 internal pages.

---

## 📈 SEO Checklist

Before publishing a new post:

- [ ] Title under 60 characters
- [ ] Description 150-160 characters
- [ ] Target keyword identified
- [ ] Keyword in title, description, first paragraph
- [ ] 3-5 H2 section headings
- [ ] 800+ words of content
- [ ] 3-5 internal links added
- [ ] All links use descriptive text
- [ ] Callout boxes for key points
- [ ] Lists for easy scanning
- [ ] Conclusion with CTA
- [ ] Proofread for typos
- [ ] Test on mobile (responsive)

---

## 🚀 Publishing Workflow

1. **Write content** in your favorite editor (Google Docs, Notion, etc.)
2. **Convert to TSX** using the template above
3. **Test locally:**
   ```bash
   cd frontend
   npm run dev
   # Visit http://localhost:5173/blog/your-slug
   ```
4. **Check responsiveness** on mobile view
5. **Commit and push:**
   ```bash
   git add frontend/src/
   git commit -m "blog: add [post title]"
   git push origin main
   ```
6. **Submit to IndexNow:**
   ```bash
   ./scripts/submit_indexnow.sh https://homeiq.ie/blog/your-slug
   ```
7. **Share on social media** (optional)

---

## 🎯 Next Posts to Write

Based on SEO strategy:

### Priority 1 (High-Volume Keywords)
1. **"Cork vs Galway vs Limerick: Property Price Comparison"**
   - Target: "compare property prices ireland"
   - 1,500 words
   - Link to all 3 county pages

2. **"Irish Property Prices - June 2026 Market Report"**
   - Target: "irish property prices [month] [year]"
   - 2,000 words
   - Monthly recurring format
   - Charts and statistics

### Priority 2 (Expand Existing)
3. **Complete "Dublin Property Prices by Postcode"**
   - Currently just a placeholder
   - Full breakdown of all D01-D22 postcodes
   - 2,500+ words

4. **Complete "Understanding Eircode for Property Search"**
   - Currently just a placeholder
   - Full guide with examples
   - 1,500+ words

### Priority 3 (Long-Tail)
5. **"First Time Buyer's Guide to Irish Property Prices"**
   - Target: "first time buyer ireland"
   - Beginner-friendly
   - 2,000 words

6. **"How Property Price Trends Work - Ireland 2010-2026"**
   - Target: "irish property price trends"
   - Historical analysis
   - 2,500 words

---

## 💡 Tips & Best Practices

### Writing Efficiency
- **Use AI assistance** (ChatGPT, Claude) for first drafts
- **Keep a swipe file** of good examples
- **Batch write** multiple posts in one session
- **Reuse structure** across similar posts

### Maintenance
- **Update monthly reports** each month
- **Refresh old posts** annually (update stats, dates)
- **Fix broken links** quarterly
- **Monitor performance** in Google Search Console

### Engagement
- **Add social sharing** buttons (future enhancement)
- **Enable comments** (future enhancement)
- **Track popular posts** via Analytics
- **Write more** on popular topics

---

## 🔧 Future Enhancements

### Phase 2 (Nice to Have)
- [ ] RSS feed generation
- [ ] Blog post search
- [ ] Related posts section
- [ ] Author bios
- [ ] Blog categories/filters
- [ ] Share buttons (Twitter, Facebook, LinkedIn)
- [ ] Reading progress indicator
- [ ] Table of contents for long posts

### Phase 3 (Advanced)
- [ ] Comments system (Disqus or similar)
- [ ] Newsletter signup in blog
- [ ] Blog post series (multi-part guides)
- [ ] Video embeds
- [ ] Interactive charts in posts
- [ ] Guest authors

---

## ✅ Current Status

**Live URLs:**
- Blog listing: https://homeiq.ie/blog
- Example post: https://homeiq.ie/blog/how-to-use-property-price-register

**Posts Status:**
- ✅ 1 complete post (How to Use PPR)
- 🟡 2 placeholder posts (need completion)
- 📝 5+ more posts planned

**Next Steps:**
1. Complete the 2 placeholder posts
2. Write 3 high-priority posts
3. Publish 2 posts per week schedule
4. Submit all to IndexNow
5. Monitor Search Console for indexing

---

**The blog system is ready to use! Start writing and publishing today.**
