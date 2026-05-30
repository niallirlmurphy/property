# Adding Images to County Pages

## Best Approaches for County Page Images

### Option 1: Unsplash API (Recommended)

**Pros:**
- ✅ Free (5,000 requests/hour)
- ✅ High-quality photos
- ✅ Automatic attribution
- ✅ Irish landscapes available
- ✅ Dynamic loading

**Setup:**

1. **Get API key:**
   - Sign up at https://unsplash.com/developers
   - Create new application
   - Copy Access Key

2. **Add to .env:**
```bash
VITE_UNSPLASH_ACCESS_KEY=your_access_key_here
```

3. **Add to CountyContent type:**
```typescript
export interface CountyContent {
  // ... existing fields
  
  // Images
  heroImage?: {
    url: string;
    alt: string;
    credit?: string;
  };
  
  // Or use Unsplash search term
  unsplashQuery?: string; // e.g., "cork ireland landscape"
}
```

4. **Use in template:**
```typescript
// In CountyPageTemplate.tsx
{content.heroImage && (
  <div className="hero-image">
    <img 
      src={content.heroImage.url} 
      alt={content.heroImage.alt}
      loading="lazy"
    />
    {content.heroImage.credit && (
      <p className="image-credit">{content.heroImage.credit}</p>
    )}
  </div>
)}
```

**Example county data:**
```typescript
export const corkContent: CountyContent = {
  // ... other fields
  
  heroImage: {
    url: "https://images.unsplash.com/photo-xxx",
    alt: "Cork city harbor at sunset",
    credit: "Photo by John Doe on Unsplash"
  },
  
  // Or simpler:
  unsplashQuery: "cork ireland harbor",
};
```

---

### Option 2: Cloudinary (Best for Scale)

**Pros:**
- ✅ Free tier (25 GB storage, 25 GB bandwidth/month)
- ✅ Automatic optimization
- ✅ Responsive images
- ✅ CDN delivery
- ✅ Image transformations

**Setup:**

1. **Sign up:** https://cloudinary.com
2. **Upload county images** to Cloudinary
3. **Get URLs** (format: `https://res.cloudinary.com/your-cloud/image/upload/v1/cork.jpg`)

**Use in county data:**
```typescript
export const corkContent: CountyContent = {
  // ...
  heroImage: {
    url: "https://res.cloudinary.com/homeiq/image/upload/w_1200,h_400,c_fill/cork.jpg",
    alt: "Cork city and harbor"
  }
};
```

---

### Option 3: Static Assets (Simplest)

**Pros:**
- ✅ No external dependencies
- ✅ Full control
- ✅ Works offline
- ✅ No API limits

**Cons:**
- ❌ Increases repo size
- ❌ Manual optimization needed
- ❌ No CDN (unless Vercel handles it)

**Setup:**

1. **Create image directory:**
```bash
mkdir -p frontend/public/images/counties
```

2. **Add images:**
```
frontend/public/images/counties/
  ├── cork.jpg
  ├── galway.jpg
  ├── dublin.jpg
  └── ...
```

3. **Optimize images first:**
```bash
# Resize to 1200x400px
# Compress with tinypng.com or similar
# Save as WebP for better compression
```

4. **Use in county data:**
```typescript
export const corkContent: CountyContent = {
  // ...
  heroImage: {
    url: "/images/counties/cork.jpg",
    alt: "Cork harbor and city skyline"
  }
};
```

---

### Option 4: Wikimedia Commons (Free, Irish-focused)

**Pros:**
- ✅ Completely free
- ✅ Public domain images
- ✅ Excellent Irish coverage
- ✅ No attribution required (though nice to include)

**How to find images:**

1. Go to https://commons.wikimedia.org
2. Search: "Cork Ireland" or "County Cork"
3. Find high-quality image
4. Click image → "Use this file"
5. Copy direct image URL

**Example URLs:**
```typescript
export const corkContent: CountyContent = {
  heroImage: {
    url: "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xx/Cork_city.jpg/1200px-Cork_city.jpg",
    alt: "Cork city center",
    credit: "Wikimedia Commons"
  }
};
```

---

## Recommended Implementation

### For Your Use Case (26 Counties):

I recommend **Option 3 (Static Assets) + Option 4 (Wikimedia)**:

**Why:**
1. Find free images on Wikimedia Commons
2. Download and optimize them
3. Store in `/frontend/public/images/counties/`
4. Reference in county content files

**Advantages:**
- No API keys needed
- No external dependencies
- Free forever
- Works offline
- Fast loading (Vercel CDN)

---

## Step-by-Step: Adding Images Now

### 1. Update CountyContent Type

```typescript
// In countyData.ts
export interface CountyContent {
  // ... existing fields
  
  // Add this:
  heroImage?: {
    url: string;
    alt: string;
    credit?: string;
  };
}
```

### 2. Update CountyPageTemplate

```typescript
// In CountyPageTemplate.tsx, after PageHeader:
{content.heroImage && (
  <div className="county-hero-image">
    <img 
      src={content.heroImage.url} 
      alt={content.heroImage.alt}
      loading="lazy"
    />
    {content.heroImage.credit && (
      <p className="image-credit">{content.heroImage.credit}</p>
    )}
  </div>
)}
```

### 3. Add CSS

```css
/* In county-template.css */
.county-hero-image {
  width: 100%;
  max-height: 400px;
  overflow: hidden;
  border-radius: 8px;
  margin: 1rem 0 2rem 0;
  position: relative;
}

.county-hero-image img {
  width: 100%;
  height: 400px;
  object-fit: cover;
  display: block;
}

.image-credit {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin: 0;
}

@media (max-width: 768px) {
  .county-hero-image {
    margin: 0.5rem -1rem 1.5rem -1rem;
    border-radius: 0;
  }
  
  .county-hero-image img {
    height: 250px;
  }
}
```

### 4. Add Image to Cork Example

```typescript
// In cork.ts
export const corkContent: CountyContent = {
  // ... existing fields
  
  heroImage: {
    url: "/images/counties/cork.jpg",
    alt: "Cork city harbor and Saint Fin Barre's Cathedral",
    credit: "Photo: Wikimedia Commons"
  },
};
```

### 5. Find & Add Images

**For each county:**

1. **Search Wikimedia Commons:**
   - https://commons.wikimedia.org
   - Search: "County [Name] Ireland"
   - Look for landscape/cityscape photos

2. **Download & Optimize:**
   ```bash
   # Download image
   # Resize to 1200x400px
   # Compress (tinypng.com)
   # Save as: frontend/public/images/counties/[county].jpg
   ```

3. **Add to county content:**
   ```typescript
   heroImage: {
     url: "/images/counties/[county].jpg",
     alt: "Description of what's in the photo",
     credit: "Photo: Wikimedia Commons"
   }
   ```

---

## Image Guidelines

### Dimensions:
- **Width:** 1200px
- **Height:** 300-400px
- **Aspect ratio:** 3:1 or 16:5
- **File size:** <200 KB (after compression)
- **Format:** JPG or WebP

### Content:
- Show iconic landmarks or landscapes
- Avoid people (privacy/rights issues)
- Good lighting and quality
- Representative of the county
- Not overly touristy

### Examples:
- **Dublin:** O'Connell Street, Liffey, Ha'penny Bridge
- **Cork:** Harbor, city skyline, Saint Fin Barre's
- **Galway:** Salthill, Spanish Arch, Corrib
- **Kerry:** Ring of Kerry landscape, Killarney
- **Clare:** Cliffs of Moher, Burren

---

## Performance Optimization

### 1. Lazy Loading
Already implemented with `loading="lazy"` attribute.

### 2. WebP Format
Modern browsers support WebP (better compression):
```html
<picture>
  <source srcset="/images/counties/cork.webp" type="image/webp">
  <img src="/images/counties/cork.jpg" alt="Cork">
</picture>
```

### 3. Responsive Images
Serve different sizes for mobile:
```html
<img 
  srcset="
    /images/counties/cork-400.jpg 400w,
    /images/counties/cork-800.jpg 800w,
    /images/counties/cork-1200.jpg 1200w
  "
  sizes="(max-width: 768px) 400px, 1200px"
  src="/images/counties/cork-1200.jpg"
  alt="Cork"
/>
```

---

## SEO Benefits

**Images improve SEO by:**
- Increasing dwell time (users stay longer)
- Reducing bounce rate
- Image search traffic
- Rich snippets in search results

**Best practices:**
- Always include `alt` text (descriptive)
- Use descriptive filenames (`cork-harbor.jpg` not `IMG_1234.jpg`)
- Add image schema markup (optional)
- Optimize file size for fast loading

---

## Cost Comparison

| Option | Setup Time | Monthly Cost | Maintenance |
|--------|-----------|--------------|-------------|
| Unsplash API | 30 mins | $0 | None |
| Cloudinary | 1 hour | $0-49 | Low |
| Static Assets | 4-6 hours | $0 | None |
| Wikimedia | 3-5 hours | $0 | None |

**Recommendation:** Static assets + Wikimedia (one-time 3-5 hour investment, $0 forever)

---

## Quick Start Script

Want me to create a script to help you add images? I can make:

```bash
./scripts/add-county-image.sh cork https://url-to-image.jpg
```

This would:
1. Download the image
2. Resize and optimize it
3. Save to `/public/images/counties/`
4. Update the county data file

Let me know if you want this!

---

## Summary

**Best approach for you:**
1. Use Wikimedia Commons for free images
2. Download and optimize (1200x400px, <200KB)
3. Store in `/public/images/counties/`
4. Add `heroImage` to county content
5. Images cached by browser automatically

**Time:** ~10-15 mins per county × 26 counties = 4-6 hours total
**Cost:** $0
**Result:** Professional-looking pages with visual appeal

Would you like me to implement the image system and add images to Cork and Galway as examples?
