#!/bin/bash
# Submit URLs to IndexNow for instant indexing
# Usage: ./submit_indexnow.sh https://homeiq.ie/new-page

INDEXNOW_KEY="32cfaa418f6f4182aa77505f3f1815de"
HOST="homeiq.ie"

if [ -z "$1" ]; then
  echo "Usage: $0 <url>"
  echo "Example: $0 https://homeiq.ie/county/dublin"
  exit 1
fi

URL="$1"

curl -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d "{
    \"host\": \"${HOST}\",
    \"key\": \"${INDEXNOW_KEY}\",
    \"keyLocation\": \"https://${HOST}/${INDEXNOW_KEY}.txt\",
    \"urlList\": [\"${URL}\"]
  }"

echo ""
echo "✓ Submitted ${URL} to IndexNow"
