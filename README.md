# TAXI4U

TAXI4U is a fare calculation and ride workflow MVP for taxi dispatch in Cochrane, AB. The FastAPI backend handles fare estimation, ride booking, and driver dispatch. A React Native / Expo mobile app covers both the customer flow (estimate, book, track) and the driver flow (login, status, accept and complete trips).

---

## Architecture

```
Customer Mobile App
    |
    |-- HomeScreen
    |     GPS auto-detects pickup on mount (editable)
    |     Nominatim autocomplete for both pickup and dropoff
    |     "Calculate Fare" -> POST /fare/calculate
    |     Last ride card (tappable, links to status view)
    |
    |-- ResultScreen
    |     Fare estimate display (zone or distance)
    |     "Book Ride" -> POST /rides/ (auto-assignment mode)
    |     Live ride status with Refresh and Cancel buttons
    |
    `-- MapScreen
          Fetches zone polygons from GET /zones
          Live GPS tracking via expo-location
          Point-in-polygon detection runs on-device
          Shows pickup/dropoff markers + driver marker

Driver Mobile App (same app, driver login gates the flow)
    |
    |-- DriverLoginScreen
    |     Authenticates via POST /driver/login (JWT)
    |
    |-- DriverProfileScreen
    |     View profile, toggle status (offline/available/busy)
    |     One-tap location share -> POST /driver/location
    |
    `-- DriverRidesScreen
          Lists assigned rides, sorted by urgency
          Accept / Decline / Start Trip / Complete Trip actions

Backend (FastAPI, repo root)
    |
    |-- Fare engine (calculator.py, zone_mapper.py, geocoder.py, routing.py)
    |     Zone fare from fares.json matrix, or distance fare ($2/km)
    |
    |-- Ride system (routers/rides.py)
    |     Create, list, assign, auto-assign, cancel
    |
    |-- Driver system (routers/driver.py)
    |     Auth, status, location, ride lifecycle actions
    |
    `-- Assignment (utils/assignment.py)
          Finds nearest available driver by Euclidean distance
          Decline triggers auto-reassignment to next nearest (excluding decliner)
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

## Ride System

### Ride Lifecycle

```
pending -> assigned -> accepted -> in_progress -> completed
       \
        -> cancelled  (from pending only)
```

A ride starts as `pending`. Assignment (manual or auto) moves it to `assigned`. The driver accepts it (`accepted`), starts the trip (`in_progress`), and completes it (`completed`). A `pending` ride can be cancelled by the customer.

### Assignment Logic

**Manual assignment** (`POST /rides/{id}/assign`): a driver is specified by email. Driver must be active and `available`.

**Auto-assignment** (`POST /rides/{id}/auto-assign`, or `assignment_mode: "auto"` on ride creation): picks the nearest active `available` driver by straight-line distance from the pickup coordinates. Ties break by lower driver ID.

**Decline and reassignment**: when a driver declines an `assigned` ride, the ride resets to `pending`, then the system immediately tries to assign the next nearest available driver, excluding the one who declined. If no other driver is available, the ride stays `pending`.

---

## Customer Mobile Workflow

1. App opens → pickup field auto-populated from GPS (editable).
2. User types or selects dropoff via autocomplete.
3. "Calculate Fare" → fare estimate screen with zone/distance breakdown.
4. "Book Ride" → creates ride with auto-assignment; assigned driver shown if found.
5. Refresh Status button polls current ride state.
6. Cancel button available while ride is `pending`.
7. Home screen shows a tappable last-ride card for quick status check.

---

## Driver Mobile Workflow

1. Driver logs in with email and password (JWT stored securely).
2. Driver Profile screen: view account info, set status to `available`, share GPS location.
3. My Rides screen: lists all rides assigned to this driver, sorted by urgency.
4. `assigned` ride → Accept or Decline buttons.
5. `accepted` ride → Start Trip button.
6. `in_progress` ride → Complete Trip button.
7. Screen refreshes on focus and supports pull-to-refresh and a manual refresh button.

---

## API Endpoints

### Fare

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/zones` | All zone polygon definitions for the mobile map |
| `GET` | `/fare/test` | Fixed fare smoke test using hard-coded zones |
| `POST` | `/fare/calculate` | Calculate fare from two address/coord inputs |

### Rides

| Method | Path | Description |
|---|---|---|
| `POST` | `/rides/` | Create a ride; `assignment_mode: "auto"` triggers immediate nearest-driver assignment |
| `GET` | `/rides/` | List all rides |
| `GET` | `/rides/me/latest` | Latest ride created by the authenticated user |
| `GET` | `/rides/{id}` | Get a single ride by ID |
| `POST` | `/rides/{id}/assign` | Manually assign a driver by email |
| `POST` | `/rides/{id}/auto-assign` | Auto-assign the nearest available driver |
| `POST` | `/rides/{id}/cancel` | Cancel a pending ride |

### Drivers

| Method | Path | Description |
|---|---|---|
| `POST` | `/driver/login` | Authenticate; returns JWT bearer token |
| `GET` | `/driver/available` | List all active, available drivers |
| `GET` | `/driver/me` | Authenticated driver's profile |
| `GET` | `/driver/status` | Current driver status |
| `POST` | `/driver/status` | Update status (`offline` / `available` / `busy`) |
| `POST` | `/driver/location` | Update driver's GPS coordinates |
| `GET` | `/driver/location/me` | Retrieve stored driver location |
| `GET` | `/driver/rides` | Rides assigned to the authenticated driver |
| `POST` | `/driver/rides/{id}/accept` | Accept an assigned ride |
| `POST` | `/driver/rides/{id}/decline` | Decline an assigned ride; triggers reassignment |
| `POST` | `/driver/rides/{id}/start` | Start an accepted ride |
| `POST` | `/driver/rides/{id}/complete` | Complete an in-progress ride |
| `POST` | `/driver/dev/create` | Create a driver account (dev only) |

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
├── main.py                 FastAPI entry point; fare endpoints; DB table creation and migrations
├── calculator.py           Zone fare (fares.json matrix) and distance fare ($2/km)
├── zone_mapper.py          Zone detection: coordinate polygon check, keyword match
├── geocoder.py             Nominatim geocoding, Canada-only, Cochrane-anchored
├── routing.py              OSRM driving distance and duration
├── database.py             SQLAlchemy engine, session factory, Base, get_db()
├── config.py               Nominatim and OSRM base URLs
├── fares.json              Fare matrix — source of truth for zone pricing
├── pytest.ini              Sets pythonpath=. so pytest finds top-level modules
├── backend/
│   └── data/
│       └── zones.json      Zone polygon definitions — source of truth for map and detection
├── models/
│   ├── driver.py           Driver ORM model (id, name, email, status, is_active, ...)
│   ├── driver_location.py  DriverLocation ORM model (driver_id, latitude, longitude)
│   └── ride_request.py     RideRequest ORM model (status, driver_id, created_by_id, ...)
├── schemas/
│   ├── driver.py           DriverCreate, DriverLogin, DriverOut, DriverPublic, DriverStatus
│   ├── driver_location.py  LocationUpdate, LocationOut
│   └── ride_request.py     RideRequestCreate, RideRequestOut, AssignRideRequest
├── routers/
│   ├── driver.py           All /driver/* endpoints; get_current_driver() JWT dependency
│   └── rides.py            All /rides/* endpoints
├── utils/
│   ├── assignment.py       find_nearest_driver() — nearest available driver by Euclidean distance
│   ├── auth.py             bcrypt password hashing and verification
│   └── jwt.py              JWT create/verify (HS256, 24 h expiry)
├── tests/
│   └── test_assignment.py  29 tests: manual assign, auto-assign, cancel, decline/reassign
└── taxi4u-mobile/
    ├── App.js              Expo entry point
    ├── app.json            Expo config (background location explicitly disabled)
    ├── package.json        Expo SDK 54, react-navigation, react-native-maps, expo-location
    └── src/
        ├── config.js                       API_BASE — update to local machine IP before running
        ├── context/
        │   └── AuthContext.js              JWT storage; login/logout; token passed to all screens
        ├── navigation/
        │   └── AppNavigator.js             Auth-gated stack navigator
        ├── screens/
        │   ├── DriverLoginScreen.js        Driver email/password login form
        │   ├── DriverProfileScreen.js      Profile view, status toggle, location share, logout
        │   ├── DriverRidesScreen.js        Driver rides list with Accept/Decline/Start/Complete
        │   ├── HomeScreen.js               Fare estimate entry, GPS pickup, last ride card
        │   ├── MapScreen.js                Live zone map with GPS tracking and markers
        │   └── ResultScreen.js             Fare display, booking, status refresh, cancel
        ├── services/
        │   ├── api.js                      All API calls: fare, rides, driver auth, location
        │   └── backgroundLocation.js       Stub only — background tracking not implemented
        ├── data/
        │   └── zones.js                    Fetches and normalizes zone polygons for the map
        └── utils/
            └── zoneDetection.js            On-device point-in-polygon detection
```

---

## Tech Stack

### Backend

| Component | Tool |
|---|---|
| API framework | FastAPI |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (`taxi4u.db`) |
| Auth | JWT via python-jose (HS256, 24 h tokens) |
| Password hashing | bcrypt |
| Geocoding | Nominatim (OpenStreetMap) |
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
pip install fastapi uvicorn sqlalchemy "python-jose[cryptography]" bcrypt requests pytest
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

The backend reads `fares.json` and `backend/data/zones.json` via absolute paths derived from the Python source files, so those loads work regardless of the current working directory.

### Tests

```bash
python -m pytest
```

`pytest.ini` sets `pythonpath = .` so no manual `PYTHONPATH` setup is needed.

### Mobile

```bash
cd TAXI4U/taxi4u-mobile
npm install
npx expo start
```

Update `API_BASE` in `taxi4u-mobile/src/config.js` to your machine's local IP address before running on a physical device. `localhost` does not work from a device.

---

## Current Limitations

- No payment system. Fares are estimates only; no charge is collected.
- No cancellation fees.
- No push notifications. Drivers and customers must manually refresh to see status changes.
- No WebSockets or live tracking. Ride state is polled on demand.
- Background location tracking is not implemented (stub only).
- No dispatcher web UI. Assignment is triggered via the API or the mobile booking flow.
- Zone keyword coverage is narrower than polygon coverage; coordinate-based detection is more reliable than free-form text input.
- The public Nominatim API is rate-limited and intended for low-volume use.
- The public OSRM endpoint is a demo service and not production-grade.
- If geocoding or routing fails, `/fare/calculate` still returns a response; distance fare uses the 10 km fallback when needed.
