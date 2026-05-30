#!/bin/bash
# Create a new county content file from template
# Usage: ./scripts/create-county-content.sh kerry

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <county-slug>"
  echo "Example: $0 kerry"
  exit 1
fi

COUNTY_SLUG="$1"
COUNTY_NAME="${COUNTY_SLUG^}"  # Capitalize first letter
OUTPUT_FILE="frontend/src/content/counties/${COUNTY_SLUG}.ts"

if [ -f "$OUTPUT_FILE" ]; then
  echo "❌ County file already exists: $OUTPUT_FILE"
  echo "Edit it directly or delete it first."
  exit 1
fi

cat > "$OUTPUT_FILE" << EOF
import type { CountyContent } from "../countyData";

export const ${COUNTY_SLUG}Content: CountyContent = {
  name: "${COUNTY_NAME}",
  slug: "${COUNTY_SLUG}",

  metaTitle: "${COUNTY_NAME} Property Prices & Market Trends",
  metaDescription: "Explore property prices across County ${COUNTY_NAME}. View median prices, transaction volumes, and price trends from Ireland's Property Price Register.",

  intro: "County ${COUNTY_NAME} property prices in 2024... [Write 150-200 word intro with key statistics, popular areas, and YoY change]",

  marketOverview: "[Write 200-300 words about the ${COUNTY_NAME} property market. Include: urban vs rural split, popular towns, economic drivers, property types, buyer demographics, recent developments.]",

  trendsCommentary: "[Write 100-150 words about ${COUNTY_NAME} price trends. When did prices rise/fall? Which areas performed best? Any notable events affecting the market?]",

  popularAreas: [
    {
      name: "Example Town",
      slug: "example-town",
      description: "Brief description of area"
    },
    // Add 5-10 popular areas in ${COUNTY_NAME}
  ],

  faqs: [
    {
      question: "What is the average house price in County ${COUNTY_NAME}?",
      answer: "The average house price in ${COUNTY_NAME} is approximately €XXX,XXX (2024). [Add specific details about variation by area.]"
    },
    {
      question: "Which areas in County ${COUNTY_NAME} are most affordable?",
      answer: "[List 3-5 affordable areas with approximate prices]"
    },
    {
      question: "How have property prices changed in County ${COUNTY_NAME}?",
      answer: "[Describe price trends since 2010, noting key periods of growth/decline]"
    },
    {
      question: "Is County ${COUNTY_NAME} a good place to invest in property?",
      answer: "[Balanced answer discussing factors like price growth, rental demand, economic outlook, location advantages]"
    },
    {
      question: "What types of properties are common in County ${COUNTY_NAME}?",
      answer: "[Describe common property types by area - urban/suburban/rural mix]"
    }
  ],

  neighboringCounties: [
    // List neighboring county slugs (lowercase)
    // Example: "cork", "limerick", "tipperary"
  ],

  highlights: [
    // Add 4-6 key highlights about ${COUNTY_NAME} property market
    // Example: "Strong tourist economy supporting rental demand"
  ]
};
EOF

echo "✅ Created county content file: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Edit $OUTPUT_FILE and fill in all the content"
echo "2. Add import to frontend/src/content/counties/index.ts:"
echo "   import { ${COUNTY_SLUG}Content } from \"./${COUNTY_SLUG}\";"
echo "   ${COUNTY_SLUG}: ${COUNTY_SLUG}Content,"
echo ""
echo "3. Test locally:"
echo "   cd frontend && npm run dev"
echo "   Visit: http://localhost:5173/county/${COUNTY_SLUG}"
echo ""
echo "4. Commit and deploy:"
echo "   git add $OUTPUT_FILE frontend/src/content/counties/index.ts"
echo "   git commit -m \"Add ${COUNTY_NAME} county content\""
echo "   git push"
echo ""
echo "5. Submit to IndexNow:"
echo "   ./scripts/submit_indexnow.sh https://homeiq.ie/county/${COUNTY_SLUG}"
EOF

chmod +x "$OUTPUT_FILE"
