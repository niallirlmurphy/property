#!/bin/bash
# Download and add images for a county from Wikimedia Commons
# Usage: ./scripts/add-county-images.sh kerry "url1" "url2" "url3"

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <county-slug> [image-url-1] [image-url-2] [image-url-3]"
  echo ""
  echo "Examples:"
  echo "  # Add single image"
  echo "  $0 kerry \"https://upload.wikimedia.org/...jpg\""
  echo ""
  echo "  # Add multiple images"
  echo "  $0 kerry \"url1\" \"url2\" \"url3\""
  echo ""
  echo "  # Interactive mode (searches Wikimedia for you)"
  echo "  $0 kerry"
  echo ""
  exit 1
fi

COUNTY_SLUG="$1"
COUNTY_NAME="${COUNTY_SLUG^}"
IMAGE_DIR="frontend/public/images/counties"
CONTENT_FILE="frontend/src/content/counties/${COUNTY_SLUG}.ts"

# Create image directory if it doesn't exist
mkdir -p "$IMAGE_DIR"

# Check if county content file exists
if [ ! -f "$CONTENT_FILE" ]; then
  echo "❌ County content file not found: $CONTENT_FILE"
  echo "Create it first with: ./scripts/create-county-content.sh $COUNTY_SLUG"
  exit 1
fi

echo "🖼️  Adding images for County ${COUNTY_NAME}..."
echo ""

# Function to download and process image
download_image() {
  local url="$1"
  local index="$2"
  local filename="${COUNTY_SLUG}-${index}.jpg"
  local filepath="${IMAGE_DIR}/${filename}"

  echo "📥 Downloading image ${index}..."
  echo "   URL: ${url}"

  # Download image
  if command -v curl &> /dev/null; then
    curl -L "$url" -o "$filepath" --fail --silent --show-error
  elif command -v wget &> /dev/null; then
    wget "$url" -O "$filepath" -q
  else
    echo "❌ Error: curl or wget is required to download images"
    exit 1
  fi

  if [ -f "$filepath" ]; then
    local size=$(du -h "$filepath" | cut -f1)
    echo "   ✓ Saved: $filepath (${size})"
    echo "   /images/counties/${filename}"
  else
    echo "   ❌ Failed to download image"
    return 1
  fi

  echo ""
}

# If URLs provided, download them
if [ -n "$2" ]; then
  download_image "$2" 1

  if [ -n "$3" ]; then
    download_image "$3" 2
  fi

  if [ -n "$4" ]; then
    download_image "$4" 3
  fi

  echo "✅ Downloaded images for ${COUNTY_NAME}"
  echo ""
  echo "📝 Next steps:"
  echo ""
  echo "1. Add to ${CONTENT_FILE}:"
  echo ""
  echo "  heroImages: ["
  [ -n "$2" ] && echo "    {"
  [ -n "$2" ] && echo "      url: \"/images/counties/${COUNTY_SLUG}-1.jpg\","
  [ -n "$2" ] && echo "      alt: \"Description of image 1\","
  [ -n "$2" ] && echo "      credit: \"Photo: Wikimedia Commons\""
  [ -n "$2" ] && echo "    },"
  [ -n "$3" ] && echo "    {"
  [ -n "$3" ] && echo "      url: \"/images/counties/${COUNTY_SLUG}-2.jpg\","
  [ -n "$3" ] && echo "      alt: \"Description of image 2\","
  [ -n "$3" ] && echo "      credit: \"Photo: Wikimedia Commons\""
  [ -n "$3" ] && echo "    },"
  [ -n "$4" ] && echo "    {"
  [ -n "$4" ] && echo "      url: \"/images/counties/${COUNTY_SLUG}-3.jpg\","
  [ -n "$4" ] && echo "      alt: \"Description of image 3\","
  [ -n "$4" ] && echo "      credit: \"Photo: Wikimedia Commons\""
  [ -n "$4" ] && echo "    }"
  echo "  ]"
  echo ""
  echo "2. Test locally:"
  echo "   cd frontend && npm run dev"
  echo "   Visit: http://localhost:5173/county/${COUNTY_SLUG}"
  echo ""
  echo "3. Commit and deploy:"
  echo "   git add frontend/public/images/counties/${COUNTY_SLUG}-*.jpg"
  echo "   git add frontend/src/content/counties/${COUNTY_SLUG}.ts"
  echo "   git commit -m \"Add images for ${COUNTY_NAME} county page\""
  echo "   git push"
  echo ""

else
  # Interactive mode - show Wikimedia search link
  echo "🔍 Interactive Mode"
  echo ""
  echo "Find images for ${COUNTY_NAME}:"
  echo "1. Visit: https://commons.wikimedia.org/w/index.php?search=${COUNTY_NAME}+Ireland"
  echo "2. Click on a high-quality image"
  echo "3. Click 'Use this file' button"
  echo "4. Copy the direct image URL (ends with .jpg or .png)"
  echo "5. Look for sizes around 1200px wide"
  echo ""
  echo "Then run:"
  echo "  $0 $COUNTY_SLUG \"<image-url-1>\" \"<image-url-2>\" \"<image-url-3>\""
  echo ""
  echo "Recommended images for ${COUNTY_NAME}:"
  echo "  - Main city/town center"
  echo "  - Iconic landmark or building"
  echo "  - Coastal or rural landscape"
  echo ""
fi

echo "💡 Tips:"
echo "  - Use 1-3 images (flexible layout)"
echo "  - Images should be 1200px+ wide"
echo "  - Choose iconic or representative scenes"
echo "  - Wikimedia Commons images are free to use"
echo ""
