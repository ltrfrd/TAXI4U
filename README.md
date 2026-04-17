# TAXI4U Fare API

A fare calculation API for taxi dispatch in Cochrane, AB. Accepts real street addresses, geocodes them, fetches live driving distance, and returns a fare based on a zone pricing chart or a per-km distance fallback.

---

## Project Overview

TAXI4U is built on FastAPI and uses the OpenStreetMap stack for location services. It supports full address input, GPS coordinate resolution, real route distance and duration, and zone-based pricing backed by a fixed fare chart.

---

## How It Works

```
User Input (pickup + dropoff address strings)
    │
    ▼
Geocoding — Nominatim (OpenStreetMap)
    Converts each address into GPS coordinates + a normalized display_name
    │
    ▼
Routing — OSRM
    Gets real driving distance (km) and duration (minutes) between the two points
    │
    ▼
Zone Detection — zone_mapper.py
    Runs keyword matching against the geocoded display_name
    Falls back to the raw input text if geocoding failed
    │
    ▼
Fare Decision
    Both zones found in fares.json  →  zone fare  (chart lookup)
    Either zone missing from chart  →  distance fare  ($2 × route km)
    │
    ▼
API Response
    Returns fare, coordinates, route info, zone details, and detection source
```

---

## Fare Logic

### Zone Fare

`fares.json` is the single source of truth for all chart-based pricing. When both the pickup and dropoff locations are recognized as named zones in the chart, the fare is read directly from the matrix — no calculation required.

- **Airports (All)** is a regular named zone in the chart, treated identically to any other zone. There is no special airport override.
- Extra stop fee: **$4 per stop**
- Waiting fee: **$0.50/min** after the first 4 free minutes

### Distance Fare (Fallback)

If either location cannot be matched to a chart zone, the fare is calculated as:

```
fare = route_distance_km × $2.00
```

The real OSRM route distance is used when available. If routing also fails, a hardcoded fallback of 10 km is applied.

### Route Info (Always Returned)

Even on zone-fare trips, `route.distance_km` and `route.duration_minutes` are always included in the response when available, so the driver has navigation context regardless of fare type.

---

## API Endpoints

### `GET /`

Health check.

```json
{ "message": "TAXI4U Fare API is running" }
```

---

### `POST /fare/calculate`

Calculate a fare from two address strings.

**Request**

```json
{
  "pickup": "Fireside Drive, Cochrane, AB",
  "dropoff": "Rivercrest Boulevard, Cochrane, AB"
}
```

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
  "pickup_detection_source": "geocoded",
  "dropoff_detection_source": "geocoded",
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

---

## Response Fields

| Field | Description |
|---|---|
| `pickup_text` / `dropoff_text` | Original address strings from the request |
| `pickup_coords` / `dropoff_coords` | `{lat, lon, display_name}` from Nominatim, or `null` if geocoding failed |
| `pickup_detection_source` / `dropoff_detection_source` | `"geocoded"` if display_name was used for zone detection, `"raw"` if raw input was used |
| `pickup_zone` / `dropoff_zone` | Detected zone name, or `"Unknown Zone"` |
| `pickup_possible_zones` / `dropoff_possible_zones` | All zones matched from the detection text |
| `validation_status` | `"valid"`, `"ambiguous"`, or `"invalid"` |
| `route` | `{distance_km, duration_minutes}` from OSRM, or `null` if routing failed |
| `fare_type` | `"zone"` if both zones are in the chart, `"distance"` otherwise |
| `fare` | Fare breakdown — structure varies by `fare_type` |

---

## File Structure

```
TAXI4U/
├── main.py           # FastAPI app and /fare/calculate endpoint
├── calculator.py     # Fare calculation logic (zone + distance)
├── zone_mapper.py    # Keyword-based zone detection
├── geocoder.py       # Nominatim geocoding
├── routing.py        # OSRM driving distance/duration
├── fares.json        # Zone fare matrix (source of truth)
└── README.md
```

---

## Tech Stack

| Component | Tool |
|---|---|
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Geocoding | Nominatim (OpenStreetMap) |
| Routing | OSRM public API |
| Fare data | fares.json (local) |

---

## Running the Server

```bash
python -m uvicorn main:app --reload --port 8001
```

Interactive API docs (Swagger UI):

```
http://127.0.0.1:8001/docs
```

---

## Notes and Limitations

- **Nominatim rate limits**: The public Nominatim API enforces a 1 request/second limit and requires a valid `User-Agent`. For production use, self-host or use a commercial geocoding provider.
- **OSRM public instance**: The public OSRM demo server (`router.project-osrm.org`) is for testing only. Self-host OSRM for a production deployment.
- **Zone detection**: Currently keyword-based against the normalized Nominatim `display_name`. Accuracy depends on how well the geocoded address text matches zone keywords. Address-coordinate boundary mapping would improve this in future.
- **Distance fallback**: Falls back to 10 km only if both geocoding and routing fail. In normal operation the real route distance is always used.
