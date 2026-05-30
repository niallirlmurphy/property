# How to Find Working Wikimedia Commons Image URLs

## The Problem
Wikimedia Commons URLs need to be exact - you can't guess them. They must be found through the actual Wikimedia site.

## Step-by-Step Process

### 1. Find Images on Wikimedia Commons

**For Cork:**
1. Go to: https://commons.wikimedia.org/wiki/Category:Cork_(city)
2. Or search: https://commons.wikimedia.org/w/index.php?search=Cork+Ireland

**For Galway:**
1. Go to: https://commons.wikimedia.org/wiki/Category:Galway
2. Or search: https://commons.wikimedia.org/w/index.php?search=Galway+Ireland

### 2. Select a Good Image

Look for:
- ✅ High resolution (1200px+ wide)
- ✅ Landscape orientation
- ✅ Good lighting and quality
- ✅ Representative of the area
- ✅ No "Uploaded by" watermarks

Avoid:
- ❌ Portrait orientation
- ❌ Low resolution
- ❌ People close-up (privacy)
- ❌ Copyrighted images

### 3. Get the Direct Image URL

**Method A: From Image Page**
1. Click on the image
2. Click on the image again to go to the file page
3. Look for the **file history** section
4. Right-click on the dimensions (e.g., "1,200 × 400 pixels")
5. Select "Copy Link Address"

**Method B: Use "Use this file" button**
1. Click on image
2. Click "Use this file" button (right side)
3. Select size (choose 1200px or larger)
4. Copy the URL shown

### 4. Test the URL

**Before adding to your code, TEST IT:**

```bash
# Test if URL works
curl -I "<paste-url-here>"

# Should return: HTTP/2 200
# Bad response: HTTP/2 404 or 400
```

**Or test in browser:**
- Open new tab
- Paste URL
- Should show the image

### 5. Add to County Content

Once you have 1-3 working URLs:

```typescript
heroImages: [
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/.../Cork_City.jpg",
    alt: "Cork city center with River Lee",
    credit: "Photo: Wikimedia Commons"
  },
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/.../Cobh.jpg",
    alt: "Cobh Cathedral and harbor",
    credit: "Photo: Wikimedia Commons"
  }
]
```

## Wikimedia URL Patterns

Working Wikimedia URLs look like:
```
https://upload.wikimedia.org/wikipedia/commons/[hash]/[filename].jpg
```

Examples:
- `https://upload.wikimedia.org/wikipedia/commons/a/ab/Cork_City.jpg`
- `https://upload.wikimedia.org/wikipedia/commons/1/2/3/Example.jpg`

**The hash part is critical** - you can't guess it!

## Example: Finding Cork Images

### Cork City Options

**Search these categories:**
- Cork (city): https://commons.wikimedia.org/wiki/Category:Cork_(city)
- Cork County: https://commons.wikimedia.org/wiki/Category:County_Cork
- River Lee: https://commons.wikimedia.org/wiki/Category:River_Lee
- English Market: https://commons.wikimedia.org/wiki/Category:English_Market,_Cork

**Good images to look for:**
- Cork City Hall
- St Fin Barre's Cathedral
- River Lee and city bridges
- English Market interior
- Cork skyline
- Shandon bells/church

### Cobh Options
- https://commons.wikimedia.org/wiki/Category:Cobh
- Look for cathedral images
- Harbor views
- Colorful houses

### Galway Options
- https://commons.wikimedia.org/wiki/Category:Galway
- Spanish Arch
- Salthill Promenade
- Claddagh area
- Connemara landscapes

## Quick Reference: Tested Working Images

I can't pre-test these due to rate limiting, but here are LIKELY working categories:

### Cork
**Category page:** https://commons.wikimedia.org/wiki/Category:Cork_(city)
- Browse, click image, get URL

### Galway  
**Category page:** https://commons.wikimedia.org/wiki/Category:Galway
- Browse, click image, get URL

## Alternative: Use Unsplash Instead

If Wikimedia is too difficult, use Unsplash:

**Cork:**
```typescript
heroImages: [
  {
    url: "https://images.unsplash.com/photo-1590086782957-93c06ef21604?w=1200&h=400&fit=crop&q=80",
    alt: "Cork, Ireland cityscape",
    credit: "Photo: Unsplash / @username"
  }
]
```

**Unsplash URL format:**
```
https://images.unsplash.com/photo-[ID]?w=1200&h=400&fit=crop&q=80
```

To find:
1. Go to https://unsplash.com/s/photos/cork-ireland
2. Click an image
3. Right-click → "Copy image address"
4. Add parameters: `?w=1200&h=400&fit=crop&q=80`

## Testing Your Images

After adding URLs, test locally:

```bash
cd frontend
npm run dev
# Visit: http://localhost:5173/county/cork
```

Check that:
- ✅ Images load (not broken)
- ✅ Images look good
- ✅ Credits display
- ✅ Mobile responsive (resize browser)

## Common Errors

**"Images not showing" = Broken URL**
- Test URL in browser first
- Check for typos
- Verify it's the direct image URL, not the page URL

**"Images too small" = Wrong size**
- Look for 1200px+ wide versions
- Use URL parameters if available

**"Images too large/slow" = File size issue**
- Wikimedia serves optimized sizes
- Use 1200px width (not full resolution)

## Need Help?

If you can't find working URLs:
1. Try Unsplash instead (easier, reliable)
2. Download images and store locally
3. Use placeholder images temporarily

The image **system is built and ready** - you just need the right URLs!
