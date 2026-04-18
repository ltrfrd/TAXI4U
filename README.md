# TAXI4U

A fare calculation system for taxi dispatch in Cochrane, AB. A FastAPI backend accepts address input or GPS coordinates, geocodes when needed, fetches live driving distance, and returns a fare based on zone pricing or a per-km distance fallback. A React Native / Expo mobile app provides autocomplete address input, fare display, and a live driver map with real-time zone detection.

---

## Architecture

```
Mobile App (Expo / React Native)
    |
    |-- HomeScreen
    |     Autocomplete -> Nominatim (Canada-only, direct from app)
    |     Tapped suggestion stores lat/lon in selection state
    |     "Calculate Fare" sends pickup + dropoff text
    |     + optional pickup_coords / dropoff_coords if a suggestion was selected
    |
    |-- ResultScreen
    |     Displays fare, zones, route info
    |     "Open Live Map" button
    |
    `-- MapScreen
          Fetches zone polygons from backend /zones
          Live GPS tracking via expo-location
          Point-in-polygon detection runs on-device
          Shows pickup/dropoff markers + driver marker

Backend (FastAPI)
    |
    |-- Input Validation
    |     Reject empty, all-punctuation, single-character inputs early
    |
    |-- Coordinate Passthrough
    |     If pickup_coords / dropoff_coords are provided -> skip geocoding
    |     Use provided lat/lon directly
    |
    |-- Geocoding - Nominatim (OpenStreetMap)
    |     Only runs if no coordinates were provided
    |     Canada-only (countrycodes=ca)
    |     Cochrane-anchored for local/ambiguous inputs
    |
    |-- Routing - OSRM
    |     Real driving distance (km) and duration (min) between the two points
    |
    |-- Zone Detection
    |     1. Coordinate -> polygon boundary check (zones.json, high confidence)
    |     2. Geocoded display_name -> keyword match (medium confidence)
    |     3. Raw input text -> keyword match (low confidence, geocoding failed)
    |
    `-- Fare Decision
          Both zones in fare chart  -> zone fare     (fares.json matrix lookup)
          Either zone not in chart  -> distance fare ($2 x route km)
```

---

## Fare Logic

### Zone Fare

`fares.json` is the single source of truth for chart-based pricing. When both pickup and dropoff resolve to named zones in the chart, the fare is read directly from the matrix.

- Extra stop fee: **$4.00 per stop**
- Waiting fee: **$0.50 / min** after the first 4 free minutes
- `Airports (All)` is a regular named zone with no special override

### Distance Fare (Fallback)

Used when either location cannot be matched to a zone in the fare chart:

```text
fare = route_distance_km x $2.00
```

The real OSRM route distance is used when available. If routing fails, a 10 km fallback is applied.

### Route Info

`route.distance_km` and `route.duration_minutes` are returned when routing succeeds. A top-level `distance` field is always returned: it is `route.distance_km` when available, otherwise the fallback distance used for pricing.

---

## Geocoding Behavior

The geocoder (`geocoder.py`) enforces Canada-only results via Nominatim `countrycodes=ca`.

For inputs without a recognizable geographic anchor word (`cochrane`, `alberta`, `calgary`, `yyc`, etc.), three progressively broader queries are tried:

| Step | Query |
|---|---|
| 1 | `"{input}, Cochrane, Alberta, Canada"` |
| 2 | `"{input}, Alberta, Canada"` |
| 3 | `"{input}"` (still Canada-only) |

If the input already contains an anchor word, the query is used as-is.

---

## Mobile Autocomplete

Address suggestions are fetched directly from Nominatim inside the mobile app. Suggestions are debounced by 400 ms, restricted to Canada, and limited to 5 results.

Each suggestion stores:

- a readable label
- `lat`
- `lon`
- `display_name`

When the user taps a suggestion:

1. The input field is filled with the readable label.
2. The lat/lon are saved in selection state.
3. On "Calculate Fare", those coordinates are sent as `pickup_coords` / `dropoff_coords`.
4. The backend skips geocoding for that field and uses the supplied coordinates directly.

Manual typing without selecting a suggestion still works. If the user edits the text after selecting a suggestion, the saved coordinates are cleared and the backend falls back to the normal text geocoding path.

---

## Live Map

After a fare is calculated, the driver can open a live zone map from the Result screen.

- `MapScreen` fetches zone definitions from `GET /zones`
- `react-native-maps` renders the polygons
- `expo-location` tracks foreground location updates
- point-in-polygon detection runs on-device
- pickup, dropoff, and driver markers are displayed together

Background location is not implemented. `taxi4u-mobile/src/services/backgroundLocation.js` is only a stub, and `taxi4u-mobile/app.json` explicitly keeps background location disabled with:

- `isAndroidBackgroundLocationEnabled: false`
- `isIosBackgroundLocationEnabled: false`

---

## Zone Detection

Zone detection runs in three tiers:

| Source | Method | Confidence |
|---|---|---|
| `coords` | GPS coordinates checked against polygon boundaries | High |
| `geocoded` | Nominatim `display_name` matched against keyword patterns | Medium |
| `raw` | Raw user input matched against keyword patterns | Low |

Overall response confidence is:

- `high` if both pickup and dropoff detection sources are `coords`
- `medium` if at least one side is `geocoded` and neither side is `raw`
- `low` otherwise

Polygon zone definitions live in `backend/data/zones.json`. Coordinate-based detection uses a bounding-box pre-check with a small inward buffer, evaluated in priority order so smaller specific zones win when zones overlap.

---

## API Endpoints

### `GET /`

Health check.

```json
{ "message": "TAXI4U Fare API is running" }
```

### `GET /zones`

Returns all zone definitions for the mobile map.

```json
{
  "zones": [
    {
      "name": "Downtown/Quarry",
      "priority": 20,
      "color": "#f4a261",
      "polygon": [
        { "latitude": 51.183, "longitude": -114.478 },
        { "latitude": 51.183, "longitude": -114.45 },
        { "latitude": 51.2, "longitude": -114.45 },
        { "latitude": 51.2, "longitude": -114.478 }
      ]
    }
  ]
}
```

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
    "lon": -114.465,
    "display_name": "Rivercrest Boulevard, Rivercrest, Cochrane, Alberta, Canada"
  }
}
```

`pickup_coords` and `dropoff_coords` are optional. When provided, geocoding is skipped for that field.

**Response (zone fare example)**

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
    "lon": -114.465,
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
  "distance": 3.8,
  "confidence": "high",
  "fare_type": "zone",
  "method_used": "zone",
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

**Early validation error**

```json
{
  "ok": false,
  "error": "Please enter a location.",
  "pickup_error": "Please enter a location.",
  "dropoff_error": null,
  "distance": null,
  "confidence": "low",
  "method_used": null
}
```

---

## Response Fields

| Field | Description |
|---|---|
| `pickup_text` / `dropoff_text` | Original address strings from the request |
| `pickup_coords` / `dropoff_coords` | `{lat, lon, display_name}` either passed in or from Nominatim; `null` if geocoding failed |
| `pickup_detection_source` / `dropoff_detection_source` | `coords`, `geocoded`, or `raw` |
| `pickup_detection_confidence` / `dropoff_detection_confidence` | Per-side confidence values derived from the detection source |
| `distance` | Top-level distance value: route distance when available, otherwise fallback distance used for fare calculation |
| `confidence` | Overall confidence: `high`, `medium`, or `low` |
| `pickup_zone` / `dropoff_zone` | Detected zone name or `Unknown Zone` |
| `pickup_possible_zones` / `dropoff_possible_zones` | All zones matched from the detection text |
| `validation_status` | `valid`, `ambiguous`, or `invalid` |
| `route` | `{distance_km, duration_minutes}` from OSRM, or `null` if routing failed |
| `fare_type` | `zone` if both zones are in the chart, otherwise `distance` |
| `method_used` | Top-level fare method marker: `zone` or `distance`; `null` on early validation errors |
| `fare` | Fare breakdown; structure varies by `fare_type` |

---

## File Structure

```text
TAXI4U/
├── main.py
├── calculator.py
├── zone_mapper.py
├── geocoder.py
├── routing.py
├── fares.json
├── backend/
│   └── data/
│       └── zones.json
└── taxi4u-mobile/
    ├── App.js
    ├── app.json
    ├── package.json
    └── src/
        ├── config.js
        ├── navigation/
        │   └── AppNavigator.js
        ├── screens/
        │   ├── HomeScreen.js
        │   ├── ResultScreen.js
        │   └── MapScreen.js
        ├── services/
        │   ├── api.js
        │   └── backgroundLocation.js
        ├── data/
        │   └── zones.js
        └── utils/
            └── zoneDetection.js
```

---

## Tech Stack

### Backend

| Component | Tool |
|---|---|
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Geocoding | Nominatim |
| Routing | OSRM public API |
| Zone data | `backend/data/zones.json` |
| Fare data | `fares.json` |

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

```bash
cd TAXI4U
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn requests
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

The backend reads both `fares.json` and `backend/data/zones.json` via file-based absolute paths derived from the Python source files, so those loads do not depend on the current working directory.

### Mobile

```bash
cd TAXI4U/taxi4u-mobile
npm install
npx expo start
```

Update `API_BASE` in `taxi4u-mobile/src/config.js` to your machine's local IP address before running.

---

## Notes and Limitations

- The public Nominatim API is rate-limited and intended for low-volume use.
- The public OSRM endpoint is a demo service and not production-grade.
- Zone keyword coverage is still narrower than polygon coverage, so coordinate-based detection is more reliable than free-form text matching.
- If geocoding or routing fails, `/fare/calculate` still returns a response and distance fare uses the 10 km fallback when needed.
- Background location tracking is intentionally not implemented yet.
