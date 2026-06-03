#!/usr/bin/env python3
"""
Generate Open Graph image for Property Price Register page.
Simple text-based design with brand colors.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Output path
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "frontend",
    "public",
    "images",
    "ppr-og-image.jpg"
)

# Create 1200x630 image (Open Graph standard)
width = 1200
height = 630

# Brand colors from HomeIQ
bg_color = "#1a3c5e"  # Dark blue
accent_color = "#4a90e2"  # Light blue
text_color = "#ffffff"  # White

# Create image with gradient background
img = Image.new('RGB', (width, height), bg_color)
draw = ImageDraw.Draw(img)

# Create subtle gradient effect
for y in range(height):
    # Blend from dark blue to slightly lighter
    r = int(26 + (74 - 26) * (y / height) * 0.3)
    g = int(60 + (144 - 60) * (y / height) * 0.3)
    b = int(94 + (226 - 94) * (y / height) * 0.3)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# Try to use system fonts, fallback to PIL default
try:
    # macOS system fonts
    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    stats_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    site_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
except:
    try:
        # Linux fonts
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        stats_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        site_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        # Fallback to default
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        stats_font = ImageFont.load_default()
        site_font = ImageFont.load_default()

# Text content
title_text = "Ireland's Property"
title_text2 = "Price Register"
subtitle_text = "Official data from 784,000+ sales since 2010"
site_text = "HomeIQ.ie"

# Calculate positions (centered)
title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = title_bbox[2] - title_bbox[0]
title_x = (width - title_width) // 2

title2_bbox = draw.textbbox((0, 0), title_text2, font=title_font)
title2_width = title2_bbox[2] - title2_bbox[0]
title2_x = (width - title2_width) // 2

subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
subtitle_x = (width - subtitle_width) // 2

site_bbox = draw.textbbox((0, 0), site_text, font=site_font)
site_width = site_bbox[2] - site_bbox[0]
site_x = (width - site_width) // 2

# Draw text with slight shadow for depth
shadow_offset = 3

# Main title (2 lines)
y_pos = 150
# Shadow
draw.text((title_x + shadow_offset, y_pos + shadow_offset), title_text, font=title_font, fill="#00000066")
draw.text((title2_x + shadow_offset, y_pos + 100 + shadow_offset), title_text2, font=title_font, fill="#00000066")
# Main text
draw.text((title_x, y_pos), title_text, font=title_font, fill=text_color)
draw.text((title2_x, y_pos + 100), title_text2, font=title_font, fill=text_color)

# Subtitle
y_pos = 320
draw.text((subtitle_x + shadow_offset, y_pos + shadow_offset), subtitle_text, font=subtitle_font, fill="#00000066")
draw.text((subtitle_x, y_pos), subtitle_text, font=subtitle_font, fill=accent_color)

# Decorative line
line_y = 430
line_margin = 200
draw.line([(line_margin, line_y), (width - line_margin, line_y)], fill=accent_color, width=3)

# Site name at bottom
y_pos = 500
draw.text((site_x + shadow_offset, y_pos + shadow_offset), site_text, font=site_font, fill="#00000066")
draw.text((site_x, y_pos), site_text, font=site_font, fill=text_color)

# Save image
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
img.save(OUTPUT_PATH, "JPEG", quality=95, optimize=True)

print(f"✅ Open Graph image created: {OUTPUT_PATH}")
print(f"   Size: {width}x{height}px")
print(f"   Format: JPEG")
print(f"   Ready for social media sharing!")
