# TAXI4U

A fare calculation system for taxi dispatch in Cochrane, AB. A FastAPI backend accepts address input or GPS coordinates, geocodes them (Canada-only), fetches live driving distance, and returns a fare based on zone pricing or a per-km distance fallback. A React Native / Expo mobile app provides autocomplete address input, fare display, and a live driver map with real-time zone detection.

---

## Architecture

```
Mobile App (Expo / React Native)
    │
    ├── HomeScreen
    │     Autocomplete → Nominatim (Canada-only, direct from app)
    │     Tapped suggestion stores lat/lon in selection state
    │     "Calculate Fare" sends pickup + dropoff text
    │     + optional pickup_coords / dropoff_coords if a suggestion was selected
    │
    ├── ResultScreen
    │     Displays fare, zones, route info
    │     "Open Live Map" button
    │
    └── MapScreen
          Fetches zone polygons from backend /zones
          Live GPS tracking via expo-location
          Point-in-polygon detection runs on-device
          Shows pickup/dropoff markers + driver marker
    │
    ▼
Backend (FastAPI)
    │
    ├── Input Validation
    │     Reject empty, all-punctuation, single-character inputs early
    │
    ├── Coordinate Passthrough
    │     If pickup_coords / dropoff_coords are provided → skip geocoding
    │     Use provided lat/lon directly (high-confidence path)
    │
    ├── Geocoding — Nominatim (OpenStreetMap)
    │     Only runs if no coordinates were provided
    │     Canada-only (countrycodes=ca)
    │     Cochrane-anchored for local/ambiguous inputs
    │
    ├── Routing — OSRM
    │     Real driving distance (km) and duration (min) between the two points
    │
    ├── Zone Detection
    │     1. Coordinate → polygon boundary check (zones.json, high confidence)
    │     2. Geocoded display_name → keyword match (medium confidence)
    │     3. Raw input text → keyword match (low confidence, geocoding failed)
    │
    └── Fare Decision
          Both zones in fare chart  →  zone fare  (fares.json matrix lookup)
          Either zone not in chart  →  distance fare  ($2 × route km)
```

---

## Fare Logic

### Zone Fare

`fares.json` is the single source of truth for chart-based pricing. When both pickup and dropoff resolve to named zones in the chart, the fare is read directly from the matrix — no calculation needed.

- Extra stop fee: **$4.00 per stop**
- Waiting fee: **$0.50 / min** after the first 4 free minutes
- `Airports (All)` is a regular named zone — no special override

### Distance Fare (Fallback)

Used when either location cannot be matched to a zone in the fare chart:

```
fare = route_distance_km × $2.00
```

The real OSRM route distance is used when available. If routing also fails, a 10 km hardcoded fallback is applied.

### Route Info (Always Returned)

`route.distance_km` and `route.duration_minutes` are included in every response when available, regardless of fare type, so the driver always has navigation context.

---

## Geocoding Behavior

The geocoder (`geocoder.py`) enforces Canada-only results via Nominatim's `countrycodes=ca` parameter on every request. No results outside Canada are ever accepted.

For inputs that lack a recognizable geographic anchor word (`cochrane`, `alberta`, `calgary`, `yyc`, etc.), three progressively broader queries are tried in order:

| Step | Query sent to Nominatim |
|---|---|
| 1 | `"{input}, Cochrane, Alberta, Canada"` — best for local streets and areas |
| 2 | `"{input}, Alberta, Canada"` — catches airports and POIs not in Cochrane |
| 3 | `"{input}"` (bare, still Canada-only) — resolves any valid Canadian city |

If the input already contains an anchor word, the query is used as-is (no anchor appended).

**Input normalization:** leading/trailing spaces are stripped, repeated whitespace is collapsed, and inputs shorter than 2 non-space characters are rejected before any geocoding attempt.

**Examples that work correctly:**

| Input | Path | Resolves to |
|---|---|---|
| `"downtown cochrane"` | Has anchor → used as-is | Cochrane downtown |
| `"DOWNTOWN COCHRANE"` | Has anchor → used as-is | Cochrane downtown |
| `"123 riverview dr"` | Step 1 anchored | Street in Cochrane |
| `"airport"` | Step 1 empty → Step 2 | Calgary International |
| `"yyc"` | Has anchor → used as-is | YYC airport |
| `"toronto"` | Step 1 → 2 empty → Step 3 bare | Toronto, ON |
| `"vancouver"` | Step 1 → 2 empty → Step 3 bare | Vancouver, BC |

---

## Mobile Autocomplete

Address suggestions are fetched directly from Nominatim inside the mobile app — no backend involvement. Suggestions appear 400 ms after the user stops typing (debounced), restricted to Canada (`countrycodes=ca`), limited to 5 results.

Each suggestion stores the resolved `lat` and `lon` alongside its display label. When the user taps a suggestion:

1. The input field is filled with a readable label (`"Place, City, Province"`)
2. The lat/lon are saved in selection state
3. On "Calculate Fare", those coordinates are sent to the backend as `pickup_coords`/`dropoff_coords`
4. The backend skips geocoding entirely for that address — coordinates are used directly

Manual typing without selecting a suggestion still works. In that case no coordinates are sent and the backend geocodes the text string.

---

## Live Map

After a fare is calculated, the driver can open a live zone map from the ResultScreen.

**Zone polygons** — MapScreen fetches all zone definitions from the backend `GET /zones` endpoint on load. Each zone is drawn as a colored polygon using `react-native-maps`. The active zone (the one containing the driver's current position) is highlighted with a brighter stroke and fill.

**Driver location** — `expo-location` requests foreground location permission and begins watching GPS position with a 10-metre distance interval and 3-second minimum time interval. The driver's current position is shown as a gold marker on the map.

**Zone switching** — On every GPS update, `findZoneForCoordinates()` runs a point-in-polygon ray-casting check on-device against the loaded polygon set. When the driver crosses into a different zone the previous zone name and timestamp are recorded and displayed in the info card at the bottom of the screen.

**Pickup and dropoff markers** — The coordinates from the fare result are shown as green (pickup) and red (dropoff) markers. The map auto-fits to include both when the screen opens.

Zone detection on the map is fully on-device — no additional network calls are made after the initial zone polygon fetch.

---

## Zone Detection

Zone detection runs in three tiers, from highest to lowest confidence:

| Source | Method | Confidence |
|---|---|---|
| `coords` | GPS coordinates checked against polygon boundaries (zones.json) | High |
| `geocoded` | Nominatim `display_name` matched against keyword patterns | Medium |
| `raw` | Raw user input matched against keyword patterns | Low |

**Polygon zones (coordinate detection):** 23 zones defined in `backend/data/zones.json`, each with a polygon boundary, priority, and color. Coordinate-based detection uses a bounding-box pre-check with a small inward buffer, evaluated in priority order so smaller specific zones win when boundaries overlap.

**Keyword zones (text detection):** 14 zones have keyword patterns defined in `zone_mapper.py`. The remaining 9 polygon zones (Fireside Business Area, H.Land/Heritage, Willows/Rivercrest, Bow Meadows, Bow Ridge, Spring Hill, Seminary, Monterra, Sunset On/Past) are detectable only by coordinate match, not by text keyword.

**Fare-only zones:** 4 zones exist in `fares.json` but have no polygon (Airports All, GE variants, LRT Crowfoot/Tuscany). These are matched by keyword only.

---

## API Endpoints

### `GET /`

Health check.

```json
{ "message": "TAXI4U Fare API is running" }
```

---

### `GET /zones`

Returns all zone definitions. Used by the mobile map screen to draw polygons and run on-device zone detection.

```json
{
  "zones": [
    {
      "name": "Downtown/Quarry",
      "priority": 1,
      "color": "#e74c3c",
      "polygon": [
        { "latitude": 51.192, "longitude": -114.472 },
        ...
      ]
    },
    ...
  ]
}
```

---

### `POST /fare/calculate`

Calculate a fare from two location inputs.

**Request**

```json
{
  "pickup": "Fireside Drive, Cochrane, AB",
  "dropoff": "Rivercrest Boulevard, Cochrane, AB",
  "pickup_coords": {
    "lat": 51.1741,
    "lon": -114.4812,
    "display_name": "Fireside Drive, Fireside, Cochrane, Alberta, Canada"
  },
  "dropoff_coords": {
    "lat": 51.1803,
    "lon": -114.4650,
    "display_name": "Rivercrest Boulevard, Rivercrest, Cochrane, Alberta, Canada"
  }
}
```

`pickup_coords` and `dropoff_coords` are **optional**. When provided, geocoding is skipped for that address and the supplied coordinates are used directly. This is the high-confidence path used when the driver selects an autocomplete suggestion in the app.

When omitted, the backend geocodes the address string as normal.

**Response (zone fare)**

```json
{
  "pickup_text": "Fireside Drive, Cochrane, AB",
  "dropoff_text": "Rivercrest Boulevard, Cochrane, AB",
  "pickup_zone": "Fireside (Residential)",
  "dropoff_zone": "Willows/Rivercrest/Ford",
  "validation_status": "valid",
  "pickup_possible_zones": ["Fireside (Residential)"],
  "dropoff_possible_zones": ["Willows/Rivercrest/Ford"],
  "pickup_coords": {
    "lat": 51.1741,
    "lon": -114.4812,
    "display_name": "Fireside Drive, Fireside, Cochrane, Alberta, Canada"
  },
  "dropoff_coords": {
    "lat": 51.1803,
    "lon": -114.4650,
    "display_name": "Rivercrest Boulevard, Rivercrest, Cochrane, Alberta, Canada"
  },
  "pickup_detection_source": "coords",
  "dropoff_detection_source": "coords",
  "pickup_detection_confidence": "high",
  "dropoff_detection_confidence": "high",
  "route": {
    "distance_km": 3.8,
    "duration_minutes": 6.2
  },
  "fare_type": "zone",
  "fare": {
    "pickup_zone": "Fireside (Residential)",
    "dropoff_zone": "Willows/Rivercrest/Ford",
    "base_fare": 20,
    "stop_fee": 0,
    "wait_fee": 0,
    "total": 20
  }
}
```

**Early validation error (bad input)**

If either address string is empty, all punctuation, or too short, the endpoint returns immediately before geocoding:

```json
{
  "ok": false,
  "error": "Please enter a location.",
  "pickup_error": "Please enter a location.",
  "dropoff_error": null
}
```

---

### `GET /fare/test`

Fixed test trip using hardcoded zone names. Useful for verifying the fare engine and `fares.json` are working without any geocoding or routing dependency.

---

## Response Fields

| Field | Description |
|---|---|
| `pickup_text` / `dropoff_text` | Original address strings from the request |
| `pickup_coords` / `dropoff_coords` | `{lat, lon, display_name}` — either passed in or from Nominatim; `null` if geocoding failed |
| `pickup_detection_source` / `dropoff_detection_source` | `"coords"` — polygon match on supplied or geocoded coordinates; `"geocoded"` — keyword match on Nominatim display_name; `"raw"` — keyword match on raw input text |
| `pickup_detection_confidence` / `dropoff_detection_confidence` | `"high"` (coords), `"medium"` (geocoded), `"low"` (raw) |
| `pickup_zone` / `dropoff_zone` | Detected zone name, or `"Unknown Zone"` |
| `pickup_possible_zones` / `dropoff_possible_zones` | All zones matched from the detection text |
| `validation_status` | `"valid"`, `"ambiguous"` (multiple zone matches), or `"invalid"` |
| `route` | `{distance_km, duration_minutes}` from OSRM, or `null` if routing failed |
| `fare_type` | `"zone"` if both zones are in the fare chart, `"distance"` otherwise |
| `fare` | Fare breakdown — structure varies by `fare_type` (see zone fare vs distance fare shapes above) |

---

## File Structure

```
TAXI4U/
├── main.py                        # FastAPI app — /fare/calculate, /zones endpoints
├── calculator.py                  # Zone fare + distance fare calculation
├── config.py                      # External service URLs (Nominatim, OSRM) — edit to swap providers
├── zone_mapper.py                 # Keyword + coordinate-based zone detection
├── geocoder.py                    # Nominatim geocoding (Canada-only, Cochrane-anchored)
├── routing.py                     # OSRM driving distance/duration
├── fares.json                     # Zone fare matrix — 27 zones (source of truth for pricing)
├── backend/
│   └── data/
│       └── zones.json             # Zone polygons, priorities, colors — 23 zones
│                                  # (source of truth for map rendering + coord detection)
└── taxi4u-mobile/
    ├── App.js                     # Entry point — mounts AppNavigator
    ├── app.json                   # Expo config (permissions, splash, plugins)
    ├── package.json               # Dependencies (Expo 54, react-navigation, maps, location)
    └── src/
        ├── config.js              # API_BASE — update to local machine IP before running
        ├── navigation/
        │   └── AppNavigator.js    # Stack navigator: Home → Result → Map
        ├── screens/
        │   ├── HomeScreen.js      # Address input with autocomplete + fare request
        │   ├── ResultScreen.js    # Fare display + route info + Open Live Map
        │   └── MapScreen.js       # Live zone map with GPS driver tracking
        ├── services/
        │   ├── api.js             # calculateFare, fetchZones, searchAddresses (AbortSignal support)
        │   └── backgroundLocation.js  # Stub — background GPS tracking (not yet implemented)
        ├── data/
        │   └── zones.js           # Thin wrapper: fetchZones from API → sorted, normalized
        └── utils/
            └── zoneDetection.js   # Point-in-polygon (ray casting) — runs on-device
```

---

## Tech Stack

### Backend

| Component | Tool |
|---|---|
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Geocoding | Nominatim (OpenStreetMap) |
| Routing | OSRM public API |
| Zone data | `backend/data/zones.json` (polygons) |
| Fare data | `fares.json` (matrix) |

### Mobile

| Component | Tool |
|---|---|
| Framework | React Native via Expo SDK 54 |
| Navigation | react-navigation (stack) |
| Maps | react-native-maps |
| GPS | expo-location |
| Address autocomplete | Nominatim (direct from app, Canada-only) |

---

## Setup and Running

### Backend

**Requirements:** Python 3.11+, FastAPI, Uvicorn, Requests

```bash
cd TAXI4U
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install fastapi uvicorn requests
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Interactive API docs (Swagger UI): `http://127.0.0.1:8001/docs`

`--host 0.0.0.0` is required so the server accepts connections from devices on the same local network (your phone running Expo Go). Without it the server binds to `127.0.0.1` only and the mobile app cannot reach it.

The backend must be run from the `TAXI4U/` root directory — `fares.json` is loaded from a relative path.

---

### Mobile App (Expo Go)

**Requirements:** Node.js 18+, Expo Go app installed on your phone

```bash
cd TAXI4U/taxi4u-mobile
npm install
npx expo start
```

Scan the QR code with Expo Go (Android) or the Camera app (iOS).

**Important:** Update `API_BASE` in `taxi4u-mobile/src/config.js` to your machine's local IP address before running. The default `localhost` does not reach your machine from a physical device or emulator.

```bash
# Windows — find your IPv4 address
ipconfig

# Mac / Linux
ifconfig
```

Example: `export const API_BASE = 'http://192.168.1.42:8001';`

---

## Notes and Limitations

- **Nominatim rate limit:** The public Nominatim API enforces 1 request/second and requires a valid `User-Agent`. The backend uses `TAXI4U-FareCalculator/1.0` and the mobile app uses `TAXI4U-MobileApp/1.0`. For production, self-host Nominatim or use a commercial geocoding provider.
- **OSRM public instance:** `router.project-osrm.org` is a demo server — do not depend on it for production. Self-host OSRM for reliable routing.
- **Zone keyword coverage:** `ZONE_PATTERNS` has keyword definitions for 14 of 23 polygon zones. The remaining 9 zones (Fireside Business Area, H.Land/Heritage, Willows/Rivercrest/Ford, Bow Meadows, Bow Ridge, Spring Hill, Seminary, Monterra, Sunset On/Past) are detectable only via GPS coordinate matching, not via text keyword. For best zone resolution, encourage autocomplete selection over free-form typing.
- **Geocoder response caching:** Per-session in-memory cache keyed on the query string. Cache is cleared on server restart.
- **Distance fare floor:** If both geocoding and routing fail, distance fare is calculated against a hardcoded 10 km fallback. This produces a minimum fare of ~$20 and should be clearly communicated to the driver in a future UI update.
- **Forward reference in FareRequest:** `pickup_coords`/`dropoff_coords` use a string annotation to forward-reference `FareLocationCoords`. FastAPI resolves this correctly at startup via Pydantic's model rebuild mechanism, but it relies on FastAPI/Pydantic v2 behavior.
