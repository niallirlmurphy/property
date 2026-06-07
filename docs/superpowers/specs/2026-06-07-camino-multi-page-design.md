# Camino Travel Diary Multi-Page Structure

**Date:** 2026-06-07  
**Status:** Design Complete, Awaiting Implementation

## Overview

Restructure the Camino travel diary into a multi-page experience with an index page and three journey/guide pages. This design maintains the existing visual style while organizing content into logical sections.

## Problem Statement

Currently, the Camino page (`/camino`) displays only the French Way journey (Le Puy to Pamplona). We need to:
1. Add a second journey (Spanish Way: Irun to Santiago)
2. Add a planning/preparation guide page
3. Create an index page to navigate between all three sections

## Goals

- Preserve existing French Way content and styling
- Add comprehensive Spanish Way journey (all 28 stages)
- Provide practical preparation guide for future pilgrims
- Maintain consistent visual design across all pages
- Keep each page self-contained and maintainable

## Non-Goals

- Creating a shared component library (each page is independent)
- Making pages data-driven (content is hardcoded in each page)
- Adding user accounts or interactive features
- Creating a blog/CMS system

## Site Structure

```
/camino                    → CaminoIndexPage (landing with 3 tiles)
├── /camino/french-way     → FrenchWayPage (Le Puy to Pamplona, existing)
├── /camino/spanish-way    → SpanishWayPage (Irun to Santiago, new)
└── /camino/before-you-go  → BeforeYouGoPage (planning guide, new)
```

## File Changes

### New Files
1. `frontend/src/pages/CaminoIndexPage.tsx` - Index with navigation tiles
2. `frontend/src/pages/SpanishWayPage.tsx` - Spanish Way journey diary
3. `frontend/src/pages/BeforeYouGoPage.tsx` - Planning guide

### Renamed Files
1. `frontend/src/pages/CaminoPage.tsx` → `frontend/src/pages/FrenchWayPage.tsx`

### Modified Files
1. `frontend/src/main.tsx` - Update routing configuration

## Page Designs

### 1. CaminoIndexPage (`/camino`)

**Purpose:** Landing page that allows visitors to choose which journey or guide to view.

**Layout:**
- **Hero Section:**
  - Full-screen parallax hero with Camino-themed background
  - Title: "Camino de Santiago Journeys"
  - Subtitle: "Personal accounts of walking the ancient pilgrimage routes across France and Spain"
  - Back to HomeIQ link (top-left)
  - Progress bar at top (scrolling indicator)

- **Navigation Tiles (3-column grid on desktop, stacked on mobile):**

  **Tile 1: The French Way**
  - Route: "Le Puy-en-Velay → Pamplona"
  - Stats: "850km • 28 days • March-April 2012"
  - Visual: Mountain/Pyrenees background image
  - Gradient overlay: amber-500 to orange-600
  - Hover: Scale up, enhanced shadow
  - Link: `/camino/french-way`

  **Tile 2: The Spanish Way**
  - Route: "Irun → Santiago (Camino del Norte)"
  - Stats: "817.5km • 31 days • May 2015"
  - Visual: Coastal/San Sebastian background image
  - Gradient overlay: blue-500 to teal-600
  - Hover: Scale up, enhanced shadow
  - Link: `/camino/spanish-way`

  **Tile 3: Before You Go**
  - Subtitle: "Planning & Preparation Guide"
  - Description: "Essential tips for walking the Camino"
  - Visual: Icon-based (backpack/compass) instead of photo
  - Gradient overlay: emerald-500 to green-600
  - Hover: Scale up, enhanced shadow
  - Link: `/camino/before-you-go`

**Visual Style:**
- Same typography as existing Camino pages (font-black headings, prose styles)
- Consistent color palette with gradient overlays
- White cards with rounded-3xl corners and shadow-2xl
- Stone-50 background color
- Responsive grid (3 columns desktop, 1 column mobile)

**Navigation:**
- Back to HomeIQ button (top-left, same as other pages)
- Scroll progress indicator (top edge)

---

### 2. FrenchWayPage (`/camino/french-way`)

**Purpose:** Display the existing Le Puy to Pamplona journey diary.

**Changes:**
- Rename file from `CaminoPage.tsx` to `FrenchWayPage.tsx`
- Update route in `main.tsx` from `/camino` to `/camino/french-way`
- Change "Back to HomeIQ" link to go to `/camino` (index page) instead of `/`
- Update link text: "Back to Camino Journeys" or "← All Journeys"
- No other content or styling changes

**Content:** (existing, no changes)
- 9 featured days from the French Way
- Hero with stats
- Journey timeline
- Pull quotes
- Conclusion section

---

### 3. SpanishWayPage (`/camino/spanish-way`)

**Purpose:** Display the complete Irun to Santiago journey diary (all 28 stages).

**Hero Section:**
- Full-screen parallax hero
- Background: Coastal scene (San Sebastian bay or similar)
- Title: "Walking the Spanish Way"
- Subtitle: "817.5 kilometers along Spain's northern coast from Irun to Santiago on the Camino del Norte"
- Stats grid (4 items):
  - Date: "May 2015"
  - Distance: "817.5km"
  - Stages: "31 days"
  - Route: "Coastal"
- Navigation: "← Back to Camino Journeys" (links to `/camino`)
- Scroll indicator
- Progress bar (top edge)

**Introduction Section:**
- White card with prose styling
- Opening paragraph from source document:
  - "There are all sorts of alternative ways of doing the Camino..."
  - Explains Camino del Norte vs Camino Frances
  - Mentions scenic coastal route through San Sebastian, Bilbao, Santander
  - Notes: "The climbs are tougher than the Camino Frances but as the saying goes 'no pain no gain'"

**Featured Stories - All 28 Stages:**

Magazine-style grid layout (same as French Way):
- Alternating image left/right
- Each stage includes:
  - **Image**: Photo or placeholder (aspect ratio 4:3)
  - **Stage badge**: "Stage [N]" with gradient background
  - **Distance badge**: "[X]km" with footprints icon
  - **Title**: "Stage [N]: [Start] to [Destination]"
  - **Excerpt**: 1-2 sentence teaser
  - **Full content**: Expandable via "Read Full Story" button
  - **Gradient theming** by region:
    - Stages 1-6 (Basque Country): Green gradients (emerald-500)
    - Stages 7-14 (Cantabria): Blue gradients (blue-500)
    - Stages 15-24 (Asturias): Teal gradients (teal-500)
    - Stages 25-28 (Galicia): Purple gradients (purple-500)

**Stage Content Mapping:**

1. **Stage 1: Irun to San Sebastian (26.5km)**
   - Excerpt: "First day. Brutal climbs. 1000 steps up a cliff. Views over Bay of Biscay. San Sebastian on fire with Friday night crowds."
   - Full: Day 1 content from source

2. **Stage 2: San Sebastian to Zumaia (30km+)**
   - Excerpt: "Over a stage and a half. Walking on the coast. Passing Zarautz. Zumaia smack in the centre for 20 euros."
   - Full: Day 2 content

3. **Stage 3: Zumaia to Markina-Xemein (40km+)**
   - Excerpt: "One of the hardest days. Fell twice in the muck. 915m ascent in rain and mist. 10 rough hours. Matron trouble at the convent."
   - Full: Day 3 content

4. **Stage 4: Markina-Xemein to Gernika (25km)**
   - Excerpt: "Meet Brian, Rosemary, and Jim from Ireland. Monster dogs, Muslim signs. The Basque are merchants and industrialists."
   - Full: Day 4 content

5. **Stage 5: Gernika to Bilbao (35.5km)**
   - Excerpt: "Worst day of muck. 835m climb. Jim tells his wife three times how much he loves her. Farewell to Brian and Rosemary."
   - Full: Stage 5 content

6. **Stage 6: Bilbao to Pobena (22km)**
   - Excerpt: "Waymarking score: 5 out of 5 (useless). Walking alone. 17 beds, over 40 pilgrims. Germans explain their shopping bags."
   - Full: Stage 6 content

7. **Stage 7: Pobena to Castro-Urdiales (17.5km)**
   - Excerpt: "Beautiful day. Mist rising in Bay of Biscay. Spectacular cliff paths. Castro-Urdiales is special. Room for 40 euros."
   - Full: Stage 7 content

8. **Stage 8: Rest Day in Castro-Urdiales**
   - Excerpt: "Feet needed a break. Got 'dipped' - mobile phone stolen. Mickey mouse replacement. Plate of squid for 7 euros."
   - Full: Stage 8 content

9. **Stage 9: Castro-Urdiales to Laredo (30km)**
   - Excerpt: "Up early. Girl wobbling at 7am. Arrived at noon. Franciscan monastery for 13 euros. Football team marching. Bilbao vs Barcelona."
   - Full: Stage 9 content

10. **Stage 10: Laredo to Guemes (30km)**
    - Excerpt: "Ferry at 9am. Prison that goes on forever. Beach for miles. Offaly gang! Ernesto's hostel with theology lecture and communal dinner."
    - Full: Stage 10 content

11. **Stage 11: Guemes to Santander (24km)**
    - Excerpt: "With Offaly gang. Ferry from Somo. City is fine but not my #1. They paid for my meal. Saying goodbye."
    - Full: Stage 11 content

12. **Stage 12: Santander to Santillana del Mar (32.5km)**
    - Excerpt: "Up at 6:30. Mountains at 1,300m. Tourists rush for photos with the pilgrim. Beautiful Pension for 20 euros. First menu del dia."
    - Full: Stage 12 content

13. **Stage 13: Santillana del Mar to Comillas (23km)**
    - Excerpt: "Omelette for 2.25 euros. Gaudi's work everywhere. Nice room for 35 euros. Dogs and kids playing while parents watch from cafe."
    - Full: Stage 13 content

14. **Stage 14: Comillas to Buelna (28.5km+)**
    - Excerpt: "Railway bridge shortcut across river. Perfect hostel in Buelna. Dutchman speaks 5 languages. Austrian taxi driver drinks too much."
    - Full: Stage 14 content

15. **Stage 15: Buelna to Ribadesella (42km)**
    - Excerpt: "Almost 50km in the guide. Rain. Dutchman leads. I split at 33km and push on alone. Arrived after 42km. Beautiful man at Hotel Marina."
    - Full: Stage 15 content

16. **Stage 16: Ribadesella to Villaviciosa (42km)**
    - Excerpt: "Sebrayo is an outpost with water and a bed. Not spending Saturday there. 42km to Villaviciosa. Hill Billy night - no sleep."
    - Full: Stage 16 content

17. **Stage 17: Villaviciosa to Gijon (35.5km)**
    - Excerpt: "Gigantic bowl. Pumping sweat on two climbs. French woman: 'You're looking for miracles - he never mentioned God in three weeks.'"
    - Full: Stage 17 content

18. **Stage 18: Gijon to Aviles (24.5km)**
    - Excerpt: "Industrial territory. Miles of massive factories. Author calls it ugly - they make products we all enjoy. Evangelical man in hostel."
    - Full: Stage 18 content

19. **Stage 19: Aviles to Soto de Luna (39km)**
    - Excerpt: "Misty. Detour gone wrong. Road ends on stilts in the air. 45km+ day. Found hostel run by publican. Fionnan from Dunshaughlin!"
    - Full: Stage 19 content

20. **Stage 20: Soto de Luna to Luarca (36km)**
    - Excerpt: "Bad marking. French snorers - found one earplug. Beautiful seaside town in a basin. Steps everywhere down to marina."
    - Full: Stage 20 content

21. **Stage 21: Luarca to La Caridad (31km)**
    - Excerpt: "Young guy zooms past easily. American Norman teaching English. Beautiful hostel for 10 euros. Bread and cheese for dinner."
    - Full: Stage 21 content

22. **Stage 22: La Caridad to Ribadeo (21.5km)**
    - Excerpt: "German brothers gone - ankle injury. Drift onto coastal route by mistake. Ribadeo in Galicia. Boss shakes hands, walks me out of town."
    - Full: Stage 22 content

23. **Stage 23: Ribadeo to Lourenza (27.5km)**
    - Excerpt: "Boss at hotel at 7am to shake hands. 1000-year-old monastery. Cute woman drags me to marble room. 38 euros. Major dislike to plastic money."
    - Full: Stage 23 content

24. **Stage 24: Lourenza to Gontan (24km)**
    - Excerpt: "Boss on balcony wishing me well. Fridge topped up. Hardest climb in Spain. Dying villages. Ernesto lecture with no mention of God."
    - Full: Stage 24 content

25. **Stage 25: Gontan to Baamonde (40km)**
    - Excerpt: "40km in 3pm. Big angry American: 'This Camino is shit.' Screams for a taxi. Fine hostel. Guide says walk 1km extra - I ignore it."
    - Full: Stage 25 content

26. **Stage 26: Baamonde to Miraz (14.5km)**
    - Excerpt: "Doss day. UK volunteers run old priest's house. 8 euros for bed and breakfast. Meditation request - 33% show up. Pierre must go."
    - Full: Stage 26 content

27. **Stage 27: Miraz to Sobrado dos Monxes (25.5km)**
    - Excerpt: "High point. 1000-year-old Cistercian monastery. 8 euros. Vespers with monks. Forgot washing - volunteers folded it for me."
    - Full: Stage 27 content

28. **Stage 28: Sobrado to Santa Irene (40km)**
    - Excerpt: "Cross country to join French Way. Blocklayer wrong. Detour of the detour. Scythes and gabhlogs. Asbestos everywhere. Doctor Mitchell."
    - Full: Stage 28 content

29. **Stage 29: Santa Irene to Santiago (20km)**
    - Excerpt: "Numbers explode on French Way. Helen from AIB, Paul from Deloitte. Queue for credentials. Menu del dia for 12 euros. Bus to airport 3 euros."
    - Full: Stage 29 content (arrival in Santiago)

**Pull Quotes (scattered between stages):**

1. After Stage 12:
   - Quote: "The mountains are beautiful but god you need to be back in civilisation every so often."
   - Context: Day 12, rest in Cahors

2. After Stage 20:
   - Quote: "I am a pilgrim that is what I signed up to."
   - Context: Franciscan priest talking about moving parish every 5-6 years

3. After Stage 26:
   - Quote: "For some it is give it to me give it to me and I give nothing back."
   - Context: Pilgrims who didn't attend meditation but expected volunteer help

**Journey Stats Section:**
- 3 stat cards:
  - **31 Stages**: "Irun to Santiago" | "817.5km total"
  - **The Offaly Gang**: "Denis, Lil, Josie, Charlie, Bridget, Jim" | "Met on the trail"
  - **Joyce's Irish Pub**: "In rural France!" | "Investigated thoroughly"

**Conclusion Section:**
- Dark gradient card (stone-900 to stone-800)
- Title: "The Northern Way"
- Content: Summary paragraph about the spectacular scenery, tougher climbs, and the need for hard training
- Note about meeting fewer English speakers
- Closing: "Thanks to everyone that helped."

**Footer:**
- "A personal travel diary"
- "May 2015"

---

### 4. BeforeYouGoPage (`/camino/before-you-go`)

**Purpose:** Provide practical planning and preparation information for future pilgrims.

**Hero Section:**
- Full-screen hero with backpack/preparation themed background
- Title: "Before You Go"
- Subtitle: "Essential planning and preparation for walking the Camino"
- Badge: "Planning Guide" (emerald gradient)
- Navigation: "← Back to Camino Journeys"
- Scroll indicator

**Introduction:**
- Brief paragraph about the importance of preparation
- Note that this guide applies to both French and Spanish routes

**Content Sections (white cards with clear hierarchy):**

**1. Pilgrim Passport**
- Icon: Document/passport icon
- Content:
  - Get from Irish Office of Confraternity of St. James
  - Stamped at each overnight location
  - Hostels check you're a genuine pilgrim
  - Certificate in Santiago requires:
    - Minimum last 100km walked (200km for cyclists)
  - **The Three Irish Stamps:**
    1. St. James's Gate - Guinness tour receptionist
    2. Local church
    3. Hedigan's Brian Boru pub, Glasnevin, Dublin
  - Ready for journey with blessings of St. James and Brian Boru

**2. Fall Back Plans**
- Icon: Plane icon
- Content:
  - If you need to end your journey:
    - **Airports**: Biarritz, Bilbao, Santander, Santiago
    - Flights to Ireland and most countries
    - Good train and bus services to airports

**3. Following the Signs**
- Icon: Direction signs icon
- Content:
  - **Shell sign with converging lines**:
    - In Galicia: follow direction where lines diverge (to the right)
    - Rest of Spain: follow direction where lines converge (to the left)
  - **Yellow arrows** painted on walls (most common)
  - **If you miss a turn**:
    - Two consecutive junctions with no signs = you missed something
    - Go back and look for sign you missed
  - Sometimes signs contradict - follow the yellow arrow

**4. Types of Accommodation**
- Icon: Bed icon
- Content:
  - **Albergue**: Hostel in Spain
  - **Hostal**: Unclassified cheap hotel (NOT a hostel)
  - **Three types of hostels**:
    1. **Local council** - municipal hostels
    2. **Religious** - run by volunteers (beautiful human beings)
    3. **Private** - most responsive, open all the time, provide food/drink
  - **Donation-based hostels**:
    - Bring 5 or 10 euro notes (not 20s)
    - No change given
  - **General rule**: No pre-booking hostels in Spain
  - Exception: Pre-book in major cities like San Sebastian
  - **Strategy**: Stay in hostels 50%+ of time to meet people
  - Try a Rural Casa (country house) at least once - beautiful, European-funded

**5. Getting to Irun (from Ireland)**
- Icon: Plane/bus icon
- Content:
  - **Flight**: Ryanair Dublin → Biarritz
  - **Bus 816**: Biarritz airport → Hendaye (~1 hour, €2)
    - Get timetable from information desk
    - Exit airport, turn left, stop 10 yards up
    - Must flag down the bus
    - Get off at Gare de Hendaye (train station)
  - **Eusko Tren**: Hendaye → Irun (€1.65, two stops)
    - Small lovely train
    - Station on left of main station
    - Goes west to Bilbao, stopping everywhere
    - To Bilbao: less than €10
  - **Taxi option**: Hendaye → Irun (~€10)
  - **Accommodation in Irun**: Albergue de Peregrinos, Calle Lucas de Berroa

**6. When You Arrive in a Town**
- Icon: Map icon
- Content:
  - **Use Cicerone guide**:
    - Tells you how to get to hostel
    - Hostel in each stage
  - **Finding accommodation**:
    - Hotels and pensions cluster near main square
    - Ask a publican (bar owner)
    - Pensions often on 2nd floor - not obvious at ground level
    - May need to press buzzer, reception answers in Spanish
    - Ask "¿Qué piso?" (what floor is reception?)
  - **Tourist office**:
    - Ask for map
    - Ask them to pencil in Camino route
    - Ask for Biblioteca (library) location for free internet
    - Libraries closed 2pm-4pm+
    - Tourist office won't call pensions on your behalf
  - **Language**:
    - Most locals have no English
    - Use clear Spanish words or gestures
    - Don't speak English sentences

**7. What to Bring - Comprehensive Checklist**
- Icon: Backpack icon
- Organized by category with checkboxes:

**Head:**
- [ ] Broad rim hat
- [ ] Sunglasses
- [ ] 2 pairs of glasses/specs

**Clothing:**
- [ ] 2 non-stick vests
- [ ] 3 t-shirts
- [ ] Normal shirt
- [ ] Fleece
- [ ] Rain gear / cape
- [ ] 2 light trousers
- [ ] 3 underwear

**Footwear:**
- [ ] Walking boots
- [ ] Sandals
- [ ] 3 pairs non-slip socks

**Gear:**
- [ ] Walking pole
- [ ] One half-litre water container
- [ ] Sleeping bag
- [ ] Plastic bags
- [ ] Head torch

**Navigation:**
- [ ] Compass
- [ ] Dictionary (Spanish)
- [ ] Guide book (Cicerone)
- [ ] Personal notes re: accommodation, flights, fall back plans

**Technology:**
- [ ] Mobile phone with camera
- [ ] Charger
- [ ] Socket adapter
- [ ] Music downloads
- [ ] Apps

**Medical (from Reddy's Pharmacy, Mobhi Rd):**
- [ ] Antibiotic tablets
- [ ] Blister pads
- [ ] Anti-swelling tablets
- [ ] Sun block / sun cream
- [ ] Tube with needle
- [ ] Scissors and thread

**Toiletries & Tools:**
- [ ] Razor
- [ ] Shampoo
- [ ] Pen knife
- [ ] Safety pins

**Documents:**
- [ ] Pilgrim passport
- [ ] Pen

**8. Key Differences: Northern vs French Route**
- Icon: Mountain icon
- Content:
  - **Scenery**: Spectacular, exceeds expectations
  - **Climbs**: Non-stop tough climbs and descents
  - **Training**: You NEED to train very hard (French route is more forgiving)
  - **People**: Fewer walkers, may go days without meeting English speakers
  - **Wilderness**: Absolute wilderness especially week one
  - If you take wrong turn, may be no houses to check with
  - **Social strategy**: Stay in hostels 50%+ to meet core group
  - **Shell sign**: Interpreted differently in Galicia vs rest of Spain (see section 3)

**9. In Summary**
- Pull quote card with key takeaways:
  - "The scenery in the Northern route is spectacular exceeding my expectations but these beautiful mountains and valleys everywhere have a price ie there are non stop tough climbs and tough descents."
  - "You will get away with a bit of training in the French Camino but up North you need to have trained very hard."

**Footer:**
- "Planning guide for the Camino"
- Link back to index: "View all journeys →"

---

## Visual Design Consistency

All pages share:
- **Typography**: Same font stack, font-black headings, prose styles
- **Color palette**: 
  - Background: stone-50
  - Cards: white with shadow-2xl
  - Primary gradients: amber/orange for French, blue/teal for Spanish, emerald/green for guide
  - Text: stone-900 (headings), stone-700 (body), stone-600 (secondary)
- **Spacing**: Consistent padding (px-6, py-16/py-24)
- **Borders**: rounded-3xl for cards, rounded-2xl for smaller elements
- **Icons**: Lucide React icons throughout
- **Hover effects**: scale-105, enhanced shadows
- **Responsive**: Mobile-first, grid layouts collapse to single column

## Navigation Flow

```
HomeIQ (/)
    ↓
Camino Index (/camino)
    ↓
    ├─→ French Way (/camino/french-way) ──→ Back to Index
    ├─→ Spanish Way (/camino/spanish-way) ──→ Back to Index
    └─→ Before You Go (/camino/before-you-go) ──→ Back to Index
```

Each journey page has:
- "← Back to Camino Journeys" link to index
- NOT "Back to HomeIQ" (that's only on the index)

## Image Handling

**French Way:**
- Existing images in `/public/camino/` directory
- Keep as-is

**Spanish Way:**
- Will need 28+ images for stage photos
- Use placeholder approach:
  - Default placeholder: coastal/mountain scene
  - If specific images available, map to stages
  - Graceful fallback if image missing
- Suggested approach: All stages use 2-3 rotating placeholder images until real photos added

**Index Page:**
- 3 tile background images needed:
  1. French Way: Mountain/Pyrenees scene (can reuse existing `/camino/image9.jpeg`)
  2. Spanish Way: Coastal/beach scene (placeholder or stock image)
  3. Before You Go: Icon-based (no photo needed)

**Before You Go:**
- Hero background: Backpack/preparation themed (stock image or abstract)
- Icons for each section (Lucide React icons)

## Implementation Notes

### Routing Configuration

In `frontend/src/main.tsx`:

```tsx
// Remove old route:
// <Route path="/camino" element={<CaminoPage />} />

// Add new routes:
<Route path="/camino" element={<CaminoIndexPage />} />
<Route path="/camino/french-way" element={<FrenchWayPage />} />
<Route path="/camino/spanish-way" element={<SpanishWayPage />} />
<Route path="/camino/before-you-go" element={<BeforeYouGoPage />} />
```

### File Renaming

1. Rename `CaminoPage.tsx` → `FrenchWayPage.tsx`
2. Update import in `main.tsx`
3. Update internal navigation link from `/` to `/camino`

### Expandable Story Pattern

Each stage uses same pattern as French Way:

```tsx
const [selectedDay, setSelectedDay] = useState<number | null>(null);

// In render:
{selectedDay === stageNumber && (
  <div className="prose prose-lg prose-stone max-w-none pt-4 border-t-2 border-stone-200">
    {stage.content.split('\n\n').map((paragraph, pIdx) => (
      <p key={pIdx}>{paragraph}</p>
    ))}
  </div>
)}

<button onClick={() => setSelectedDay(selectedDay === stageNumber ? null : stageNumber)}>
  {selectedDay === stageNumber ? 'Show Less' : 'Read Full Story'}
</button>
```

### Stage Data Structure

```tsx
interface StageEntry {
  stage: number;
  title: string;
  distance: string;
  route: string; // e.g., "Irun to San Sebastian"
  excerpt: string;
  content: string;
  image?: string;
  region: 'basque' | 'cantabria' | 'asturias' | 'galicia';
}
```

### Gradient Mapping

```tsx
const regionColors = {
  basque: 'from-emerald-400 to-green-500',
  cantabria: 'from-blue-400 to-cyan-500',
  asturias: 'from-teal-400 to-cyan-500',
  galicia: 'from-purple-400 to-pink-500',
};
```

## Content Organization

### Spanish Way - 28 Stages

Content extracted from source document (Irun in Spain to Santiago May 2015.docx):
- Day 1-28 diary entries
- Each entry contains: location, distance, full narrative
- Stages mapped to regions for gradient theming
- Pull quotes extracted from memorable moments

### Before You Go - Sections

Content extracted from source document:
- "Before you Go" section
- "The signs you follow" section
- "Hostels are called Albergues" section
- "The journey to Irun" section
- "When you arrive in a town" section
- "Wealth in Basque country" context
- "Checklist of what to bring" section
- "In Summary" section

## Testing Checklist

- [ ] Index page displays 3 tiles correctly
- [ ] All 4 routes work (index + 3 sub-pages)
- [ ] Navigation links work (back to index, back to HomeIQ)
- [ ] French Way content unchanged from original
- [ ] Spanish Way displays all 28 stages
- [ ] Expandable stories work (click to expand/collapse)
- [ ] Before You Go displays all 9 sections
- [ ] Responsive layout works on mobile
- [ ] Images load correctly (or fallback gracefully)
- [ ] Scroll progress bar works on all pages
- [ ] Hero parallax effect works
- [ ] Hover effects work on tiles and buttons

## Future Enhancements (Out of Scope)

- Add photo galleries for each stage
- Add interactive map with route overlay
- Add comments/testimonials from other pilgrims
- Create printable PDF versions
- Add email capture for "planning your Camino" guide
- Multi-language support (Spanish/French)
- Add more Camino routes (Portuguese Way, Primitivo, etc.)

## Success Criteria

- Users can navigate between all three sections from index
- Each journey maintains consistent visual style
- Spanish Way comprehensively documents all 28 stages
- Before You Go provides practical actionable information
- Existing French Way content preserved and functional
- Mobile experience is smooth and readable
- Page load times remain fast (<3s)

---

## Appendix: Stage Distance Summary

Total: 817.5km over 31 stages (some rest days)

**Basque Country (Stages 1-6):** 159km
- Stage 1: 26.5km
- Stage 2: 30km+ (unofficial)
- Stage 3: 40km+ (unofficial)
- Stage 4: 25km
- Stage 5: 35.5km
- Stage 6: 22km

**Cantabria (Stages 7-14):** 215km
- Stage 7: 17.5km
- Stage 8: Rest day
- Stage 9: 30km
- Stage 10: 30km
- Stage 11: 24km
- Stage 12: 32.5km
- Stage 13: 23km
- Stage 14: 28.5km+

**Asturias (Stages 15-24):** 335km
- Stage 15: 42km
- Stage 16: 42km
- Stage 17: 35.5km
- Stage 18: 24.5km
- Stage 19: 39km
- Stage 20: 36km
- Stage 21: 31km
- Stage 22: 21.5km
- Stage 23: 27.5km
- Stage 24: 24km

**Galicia (Stages 25-28):** 108.5km
- Stage 25: 40km
- Stage 26: 14.5km
- Stage 27: 25.5km
- Stage 28: 40km (to Santa Irene)
- Stage 29: 20km (to Santiago)

---

**End of Design Document**
