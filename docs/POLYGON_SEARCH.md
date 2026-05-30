# Polygon Search Feature

**URL**: https://homeiq.ie/polygon

Map-based property search using drawing tools to define custom search areas.

## Features

### Interactive Map
- **Full-width layout**: Map takes entire viewport width with controls at bottom
- **OpenStreetMap tiles**: Free, open-source map tiles
- **Smooth navigation**: Pan, zoom, and fly-to animations
- **Responsive**: Adapts to different screen sizes

### Drawing Tools (Top-Left Panel)

**Available shapes:**
1. **Polygon** 🔷
   - Draw custom multi-point shapes
   - Click to add points, double-click to finish
   - Shows area in square meters
   - Flexible for irregular areas

2. **Rectangle** ⬛
   - Click and drag to create rectangular area
   - Quick for grid-aligned searches
   - Perfect for urban areas

3. **Circle** ⭕
   - Click center, drag to set radius
   - Converts to radius-based search (existing API)
   - Good for "within X km" searches

4. **Delete** 🗑️
   - Remove drawn shapes
   - Clears search results

### Region Navigation (Bottom Panel)

**Quick jump dropdown with:**
- **26 Irish counties**: Carlow, Cavan, Clare, Cork, Donegal, Dublin, Galway, Kerry, Kildare, Kilkenny, Laois, Leitrim, Limerick, Longford, Louth, Mayo, Meath, Monaghan, Offaly, Roscommon, Sligo, Tipperary, Waterford, Westmeath, Wexford, Wicklow
- **20 Dublin postcodes**: D1-D24 (excluding D10, D19, D21, D23)

**Behavior:**
- Select region → map flies to location with smooth animation
- Zoom level: 11 (city/town level)
- Duration: 1.5 seconds

### Results Panel (Right Side)

**Displays:**
- Property count (e.g., "Found 234 properties")
- First 50 properties (performance optimization)
- For each property:
  - Address (bold)
  - Price (formatted with € symbol)
  - Sale date (localized format)
- Scrollable for long lists
- Positioned absolutely to overlay map

## Technical Implementation

### Frontend

**File**: `frontend/src/pages/PolygonSearchPage.tsx`

**Dependencies:**
```json
{
  "leaflet": "^1.9.4",
  "react-leaflet": "^4.2.1",
  "leaflet-draw": "^0.21.0",
  "@types/leaflet": "^1.9.14",
  "@types/leaflet-draw": "^1.0.8"
}
```

**Key components:**
- `MapContainer`: Main Leaflet map wrapper
- `TileLayer`: OpenStreetMap tiles
- `DrawTools`: Custom hook for Leaflet Draw integration
- `MapController`: Handles region navigation
- `MapControls`: Bottom region dropdown
- Results panel: Absolute-positioned overlay

**Map configuration:**
```typescript
center: [53.3498, -6.2603]  // Dublin city center
zoom: 7                      // Country-wide view
zoomControl: false          // Custom controls at bottom
```

### Backend

**Endpoint**: `POST /search/polygon`

**File**: `backend/main.py`

**Request schema:**
```python
class PolygonSearchRequest(BaseModel):
    coordinates: list[list[float]]  # [[lat, lon], ...]
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    limit: int = Field(500, ge=1, le=1000)
```

**Example request:**
```json
{
  "coordinates": [
    [53.35, -6.26],
    [53.35, -6.25],
    [53.34, -6.25],
    [53.34, -6.26],
    [53.35, -6.26]
  ],
  "min_price": 300000,
  "max_price": 500000,
  "min_year": 2020,
  "limit": 500
}
```

**SQL Query:**
```sql
SELECT
    id, sale_date, address, county, eircode, price,
    not_full_market_price, vat_exclusive, description,
    size_description, latitude, longitude, routing_key
FROM properties
WHERE ST_Within(geog::geometry, ST_GeomFromText('POLYGON((...))', 4326))
  AND price >= $1
  AND price <= $2
  AND EXTRACT(YEAR FROM sale_date) >= $3
  AND EXTRACT(YEAR FROM sale_date) <= $4
ORDER BY sale_date DESC
LIMIT $5
```

**PostGIS function**: `ST_Within(geometry, polygon)`
- Returns TRUE if geometry is completely inside polygon
- Uses spatial index (GIST) for fast lookups
- SRID 4326: WGS84 coordinate system (standard lat/lon)

**Response:**
```json
{
  "count": 234,
  "results": [
    {
      "id": 123456,
      "address": "10 Main Street, Dublin 2",
      "county": "Dublin",
      "eircode": "D02 XY12",
      "price": 450000,
      "sale_date": "2024-03-15",
      "latitude": 53.3415,
      "longitude": -6.2626,
      ...
    },
    ...
  ]
}
```

**Rate limiting**: 30 requests per minute per IP

### Circle Search Conversion

When user draws a circle:
1. Extract center point: `[lat, lng]`
2. Extract radius in meters: `layer.getRadius()`
3. Convert to kilometers: `radius / 1000`
4. Call existing radius search API:
   ```
   GET /search?q={lat},{lng}&radius_km={radius}
   ```

This reuses existing optimized radius search with auto-expansion logic.

## Region Centroids

Pre-calculated center points for quick navigation:

**Counties** (26):
- Sourced from geographical centers
- Zoom level: 11 (shows ~50km radius)

**Dublin Postcodes** (20):
- Based on postal district centers
- Zoom level: 11 (shows neighborhood detail)

**Example centroids:**
```typescript
"Dublin": [53.3498, -6.2603]
"Cork": [51.8985, -8.4756]
"Galway": [53.2707, -8.9630]
"Dublin 1": [53.3519, -6.2605]
"Dublin 2": [53.3398, -6.2588]
```

## Performance Considerations

### Frontend
- **Limit results to 50**: Prevents DOM overload
- **Lazy rendering**: Only visible properties rendered
- **Debounced searches**: Prevents API spam during drawing
- **Absolute positioning**: Results panel doesn't affect map layout

### Backend
- **Spatial index**: GIST index on `geog` column
- **Query optimization**: ST_Within uses index effectively
- **Limit enforcement**: Maximum 1,000 properties per query
- **Rate limiting**: 30 requests/minute prevents abuse

### Database
```sql
-- Existing spatial index
CREATE INDEX idx_properties_geog ON properties USING GIST (geog);

-- Query plan (typical)
-- Index Scan using idx_properties_geog
-- Rows Removed by Filter: 0
-- Execution Time: ~50-200ms (depends on polygon size)
```

## Usage Examples

### Search for properties in custom area
1. Navigate to `/polygon`
2. Zoom to desired location (or use region dropdown)
3. Click polygon tool
4. Click map to add points (minimum 3)
5. Double-click to finish
6. View results in right panel

### Search within neighborhood
1. Select region (e.g., "Dublin 2")
2. Map flies to area
3. Draw rectangle around neighborhood
4. Review properties within bounds

### Search within 2km of point
1. Click circle tool
2. Click map for center point
3. Drag to 2km radius
4. Results show all properties within circle

## Future Enhancements

### Planned features:
- [ ] Export results to CSV
- [ ] Save/share polygon URLs
- [ ] Multiple polygon support (union query)
- [ ] Heatmap layer (price density)
- [ ] Property markers on map
- [ ] Filter panel (price, year, type)
- [ ] Drawing tool presets (common shapes)
- [ ] Touch/mobile gestures

### Backend improvements:
- [ ] Polygon simplification (reduce vertices for large shapes)
- [ ] Caching for common regions
- [ ] Aggregation queries (avg price, count by year)
- [ ] GeoJSON export format

## Testing

### Manual tests:
```bash
# 1. Start dev servers
cd frontend && npm run dev
cd backend && uvicorn main:app --reload

# 2. Navigate to http://localhost:5173/polygon

# 3. Test drawing tools
- Draw polygon → verify results
- Draw rectangle → verify results
- Draw circle → verify circle search
- Delete shape → verify results clear

# 4. Test region navigation
- Select each county → verify map moves
- Select Dublin postcodes → verify zoom level

# 5. Test edge cases
- Polygon with no properties → shows 0
- Very large polygon → limited to 1,000 results
- Invalid coordinates → API returns 400 error
```

### API tests:
```bash
# Valid polygon search
curl -X POST http://localhost:8000/search/polygon \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [[53.35,-6.26],[53.35,-6.25],[53.34,-6.25],[53.34,-6.26],[53.35,-6.26]],
    "limit": 10
  }'

# With filters
curl -X POST http://localhost:8000/search/polygon \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [[53.35,-6.26],[53.35,-6.25],[53.34,-6.25],[53.34,-6.26],[53.35,-6.26]],
    "min_price": 300000,
    "max_price": 500000,
    "min_year": 2020,
    "limit": 10
  }'

# Invalid polygon (< 3 points)
curl -X POST http://localhost:8000/search/polygon \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [[53.35,-6.26],[53.35,-6.25]],
    "limit": 10
  }'
# Should return: 400 Bad Request
```

## Troubleshooting

### Map not loading
- Check browser console for errors
- Verify Leaflet CSS is imported
- Check network tab for tile loading errors

### Drawing tools not appearing
- Verify Leaflet Draw CSS is imported
- Check `leaflet-draw` package is installed
- Ensure DrawTools component is mounted

### No results returned
- Verify polygon has at least 3 points
- Check polygon coordinates are in Ireland bounds
- Try larger polygon area
- Check backend logs for SQL errors

### API 400 errors
- Validate coordinate format: `[[lat, lon], ...]`
- Ensure polygon closes (first point = last point)
- Check limit is between 1-1,000

### Slow searches
- Reduce polygon complexity (fewer vertices)
- Check spatial index exists: `\d properties` in psql
- Verify GIST index on `geog` column
- Consider narrower date/price filters

## Related Documentation

- Main docs: `CLAUDE.md`
- API documentation: `backend/main.py`
- Frontend types: `frontend/src/types.ts`
- Leaflet docs: https://leafletjs.com/
- Leaflet Draw: https://leaflet.github.io/Leaflet.draw/
- PostGIS ST_Within: https://postgis.net/docs/ST_Within.html
