# TAXI APP — Development Roadmap
*Cochrane, Alberta — May 2026*

---

## Stack Reference
```
Backend       FastAPI + PostgreSQL
Real-time     FastAPI WebSockets
Maps          Google Maps API
Notifications Firebase FCM
Background    ARQ + Redis
```

---

## Roadmap Philosophy

- Every step builds on the previous — no skipping
- Each step is fully tested before moving forward
- No workarounds, no patches, no technical debt
- Push to GitHub only at step completion
- Architecture decisions are locked per step

---

## PHASE 1 — Foundation

### Step 1 — Project Scaffolding
Set up the entire project structure before writing any feature code.

```
app/
  core/
    config.py       # environment variables
    enums.py        # all enums centralized
    security.py     # password hashing, JWT
    database.py     # DB session management
  models/           # SQLAlchemy models
  schemas/          # Pydantic schemas (internal + public)
  services/         # business logic
  routers/          # HTTP transport only
  background/       # ARQ job definitions
  websockets/       # WebSocket handlers
migrations/         # Alembic migration chain
tests/
```

Deliverables:
- Project structure locked
- Environment config (`.env`)
- Database connection working
- Alembic initialized (`0000_initial.py`)
- Redis connection working
- ARQ worker boots
- All dependencies installed and pinned in `requirements.txt`

---

### Step 2 — Core Enums and Base Models
Define all enums and base database models before any feature work.

Enums (all in `core/enums.py`):
```
UserRole:      ADMIN, MANAGER, DISPATCHER, DRIVER, CUSTOMER
UserStatus:    ACTIVE, INACTIVE
VehicleStatus: ACTIVE, INACTIVE
TripType:      APP_REQUEST, PHONE_REQUEST
TripStatus:    PENDING, ASSIGNED, ACCEPTED, ARRIVED,
               STARTED, COMPLETED, CANCELLED, DECLINED
```

Models:
```
User
DriverProfile
CustomerProfile
Vehicle
DriverVehicleAssignment
Zone
FareMatrix
SpecialRoute
Trip
DriverLocation
PasswordResetToken
```

### Trips Table — Full Field List

The `trips` table is the most complex in the system. All fields must be defined here to avoid mid-build migrations later.

**Identity**
```
id                    Integer, primary key
trip_type             TripType enum — APP_REQUEST | PHONE_REQUEST
status                TripStatus enum
```

**Parties**
```
customer_user_id      FK → users.id
driver_user_id        FK → users.id, nullable (not yet assigned)
dispatcher_user_id    FK → users.id, nullable (PHONE_REQUEST only)
```

**Location**
```
pickup_address        Text
dropoff_address       Text
pickup_zone_id        FK → zones.id, nullable (outside zone trips)
dropoff_zone_id       FK → zones.id, nullable (outside zone trips)
```

**Fare**
```
suggested_fare        Numeric — calculated at trip creation
final_fare            Numeric, nullable — set on completion or override
fare_overridden       Boolean, default false
stop_count            Integer, default 0
standby_minutes       Numeric, default 0
distance_km           Numeric, nullable — road distance, used for outside-zone pricing
```

**Assignment Tracking**
```
declined_count        Integer, default 0 — how many drivers declined before acceptance
```

**Timestamps**
```
assigned_at           Timestamptz, nullable
accepted_at           Timestamptz, nullable
arrived_at            Timestamptz, nullable — standby timer starts from this field
started_at            Timestamptz, nullable
completed_at          Timestamptz, nullable
created_at            Timestamptz
updated_at            Timestamptz
```

**Audit**
```
created_by_user_id    FK → users.id
updated_by_user_id    FK → users.id, nullable
```

**Ratings**
```
driver_rating         Integer, nullable — customer rates driver (1–5)
customer_rating       Integer, nullable — driver rates customer (1–5)
```

Soft delete fields applied per table:
```
users                      status: ACTIVE / INACTIVE
vehicles                   status: ACTIVE / INACTIVE
zones                      is_active
fare_matrix                is_active
special_routes             is_active
driver_vehicle_assignments is_active
```

Audit fields applied per table:
```
trips                      created_by_user_id, updated_by_user_id
vehicles                   created_by_user_id, updated_by_user_id
zones                      created_by_user_id, updated_by_user_id
fare_matrix                created_by_user_id, updated_by_user_id
special_routes             created_by_user_id, updated_by_user_id
users                      updated_by_user_id
driver_vehicle_assignments assigned_by_user_id
```

Deliverables:
- All enums defined and locked
- All models defined with correct relationships
- Trips table defined with all fields listed above
- Soft delete fields on all applicable tables
- Audit fields on all applicable tables
- Migration `0001_core_models.py` applied
- No orphaned fields, no missing foreign keys

---

### Step 3 — Authentication Module
Build the complete auth system before any other feature.

Endpoints:
```
POST  /auth/login
POST  /auth/logout
POST  /auth/refresh
GET   /auth/me
POST  /auth/forgot-password
POST  /auth/reset-password
```

Rules:
- JWT access token (30 min) + refresh token (30 days)
- Password hashing with bcrypt
- Status checked on every protected request
- INACTIVE users rejected at token validation
- Role stored in token payload
- Password reset via email token (15 min expiry)

Deliverables:
- All auth endpoints working
- Role-based access control (RBAC) dependency ready for all future routes
- Full test suite for auth flows
- Token refresh tested
- Password reset flow tested end to end

---

### Step 4 — User Management Module
MANAGER creates and manages all operational users.

Endpoints:
```
POST   /users/                  # create user (MANAGER)
GET    /users/                  # list users (MANAGER)
GET    /users/{id}              # get user (MANAGER)
PATCH  /users/{id}              # update user (MANAGER)
PATCH  /users/{id}/status       # activate / deactivate (MANAGER)
```

Customer self-registration:
```
POST   /auth/register           # customer registers on mobile app
```

Rules:
- MANAGER creates: dispatchers, drivers, customers
- CUSTOMER self-registers only
- ADMIN manages admin-level accounts only
- No internal IDs in public responses
- `updated_by_user_id` set on every update
- Driver profile auto-created on driver account creation
- Customer profile auto-created on registration
- Deactivation sets status to INACTIVE — no hard deletes

Deliverables:
- Full CRUD for users
- Role-based access enforced per endpoint
- Soft deactivation tested
- Audit field population tested
- Profile auto-creation tested
- Self-registration tested
- Full test suite

---

## PHASE 2 — Fleet Management

### Step 5 — Vehicle Module
MANAGER creates and manages the fleet.

Endpoints:
```
POST   /vehicles/               # create vehicle (MANAGER)
GET    /vehicles/               # list vehicles (MANAGER)
GET    /vehicles/{id}           # get vehicle (MANAGER)
PATCH  /vehicles/{id}           # update vehicle (MANAGER)
PATCH  /vehicles/{id}/status    # activate / deactivate (MANAGER)
```

Rules:
- No internal IDs in public responses
- Plate number must be unique
- `created_by_user_id` set on creation
- `updated_by_user_id` set on every update
- Deactivation sets status to INACTIVE — no hard deletes

Deliverables:
- Full vehicle CRUD
- Soft deactivation tested
- Audit field population tested
- Full test suite

---

### Step 6 — Driver-Vehicle Assignment Module
MANAGER assigns vehicles to drivers. Not permanent.

Endpoints:
```
POST   /assignments/                        # assign vehicle to driver (MANAGER)
POST   /assignments/{id}/unassign           # unassign (MANAGER)
GET    /assignments/driver/{driver_id}      # current assignment for driver (MANAGER)
GET    /assignments/vehicle/{vehicle_id}    # current assignment for vehicle (MANAGER)
```

Rules:
- One active assignment per driver at a time
- Assigning a new vehicle auto-closes the previous assignment
- Unassign is a soft-close — sets `is_active = false` and `unassigned_at = now()`
- Never a hard delete — historical assignments preserved
- `assigned_by_user_id` set on every assignment

Deliverables:
- Assignment logic fully tested
- Conflict handling tested (driver already assigned)
- Audit field population tested
- Full test suite

---

## PHASE 3 — Pricing Engine

### Step 7 — Zone and Fare Matrix Module
MANAGER configures all zones and pricing.

Endpoints:
```
POST   /zones/                          # create zone (MANAGER)
GET    /zones/                          # list zones (MANAGER)
PATCH  /zones/{id}                      # update zone (MANAGER)
PATCH  /zones/{id}/status               # activate / deactivate zone (MANAGER)

POST   /fares/matrix/                   # set zone pair price (MANAGER)
GET    /fares/matrix/                   # list all fare pairs (MANAGER)
PATCH  /fares/matrix/{id}               # update fare pair (MANAGER)
PATCH  /fares/matrix/{id}/status        # activate / deactivate fare pair (MANAGER)

POST   /fares/special-routes/           # create special route (MANAGER)
GET    /fares/special-routes/           # list special routes (MANAGER)
PATCH  /fares/special-routes/{id}       # update special route (MANAGER)
PATCH  /fares/special-routes/{id}/status  # activate / deactivate (MANAGER)
```

Rules:
- 26 Cochrane zones seeded on first run
- Calgary Airport special route seeded on first run ($90 fixed)
- Pricing is symmetrical — A→B stored once, lookup handles both directions
- `created_by_user_id` and `updated_by_user_id` set on all records
- No hard deletes — deactivate via `is_active`

Deliverables:
- Zone and fare matrix seeded with real Cochrane data
- Special route seeded
- Soft deactivation tested on all three tables
- Audit field population tested
- Full test suite

---

### Step 8 — Fare Calculation Engine
The core pricing logic. No endpoints — internal service only.

Logic:
```
Priority 1 — Special fixed route
  Any Cochrane zone → Calgary International Airport = $90.00

Priority 2 — Fare matrix
  Both zones within the 26 Cochrane zones = fare_matrix price

Priority 3 — Outside zone
  Dropoff outside 26 zones (excl. Calgary Airport) = $2.00/km
  Road distance stored in trips.distance_km
```

Additional fees:
```
Stop fee:       $4.00/stop
Standby charge: $0.50/min after 4 min wait (auto-triggered from arrived_at)
GST:            already included in all listed prices
```

Rules:
- Fare engine is a pure service function — no side effects
- Called at trip creation to produce `suggested_fare`
- Returns itemized breakdown internally for audit
- Customers never see pricing
- `distance_km` stored on the trip at creation for outside-zone trips

Deliverables:
- Fare engine fully tested against all 3 priority tiers
- Edge cases tested (zone boundary, airport route, outside zone)
- Stop fee and standby charge calculation tested
- `distance_km` stored correctly on outside-zone trips
- Full test suite

---

## PHASE 4 — Trip Engine

### Step 9 — Trip Creation Module

Endpoints:
```
# Customer mobile endpoints (no IDs anywhere)
POST   /trips/app                   # customer creates app trip (CUSTOMER)
GET    /trips/current               # customer's active trip (CUSTOMER)
GET    /trips/history               # customer's trip history (CUSTOMER)

# Driver mobile endpoints (no IDs anywhere)
GET    /driver/trip/current         # driver's active trip (DRIVER)
GET    /driver/trip/queued          # driver's queued (next) trip if any (DRIVER)
GET    /driver/history              # driver's trip history (DRIVER)

# Internal panel endpoints (technical, IDs allowed in URL but not shown in UI)
POST   /trips/phone                 # dispatcher creates phone trip (DISPATCHER)
GET    /trips/active                # all currently active trips (MANAGER, DISPATCHER)
GET    /trips/pending               # all trips awaiting assignment (MANAGER, DISPATCHER)
GET    /trips/by-customer/{customer_user_id}   # filter by customer (MANAGER, DISPATCHER)
GET    /trips/by-driver/{driver_user_id}       # filter by driver (MANAGER, DISPATCHER)
GET    /trips/{id}                  # full trip detail — internal use (MANAGER, DISPATCHER)
```

Rules:
- App trip: status starts at PENDING, auto-assignment triggered
- Phone trip: status starts at PENDING, dispatcher assigns manually
- Fare engine called at creation, `suggested_fare` stored
- `distance_km` stored at creation for outside-zone trips
- `dispatcher_user_id` populated only for PHONE_REQUEST
- `created_by_user_id` set on creation
- `updated_by_user_id` set on every status change
- Customer/driver endpoints resolve "current" from the authenticated user — no IDs passed
- Internal panel endpoints use IDs for routing only; the UI displays names/plates/timestamps, never the ID itself
- `trip_type` always stored — never optional
- A customer has at most one trip in `current` at a time
- A driver has at most one trip in `current` and one in `queued`

Deliverables:
- Trip creation tested for both types
- Customer mobile endpoints tested — no IDs in any response
- Driver mobile endpoints tested — no IDs in any response
- Internal panel endpoints tested
- Fare calculated and stored at creation
- `distance_km` stored on outside-zone trips
- Audit fields populated correctly
- Role access enforced per endpoint
- Full test suite

---

### Step 10 — Driver Assignment Module

Endpoints:
```
POST   /trips/{id}/assign               # dispatcher assigns driver (DISPATCHER)
POST   /trips/{id}/reassign             # dispatcher reassigns driver (DISPATCHER)
```

Auto-assignment service (internal — triggered by app trip creation):
```
Priority 1 — Nearest online ACTIVE driver with no active trip and no queued trip
Priority 2 — Nearest online ACTIVE driver with an active trip but no queued trip
Excluded   — Drivers with both an active trip AND a queued trip
Distance   — Road distance via Google Maps Distance Matrix API
Retry      — If driver declines, repeat priority logic with next nearest
No limit   — Keep trying until someone accepts (someone always has capacity)
```

Driver Queue Rules:
- A driver may hold at most: 1 active trip + 1 queued trip
- When both slots are full, the driver is excluded from auto-assignment
- The driver re-enters the assignment pool when either trip completes or is cancelled
- On COMPLETED or CANCELLED of the active trip, the queued trip becomes the new active trip

Assignment Rules:
- Auto-assignment runs as background job via ARQ
- Manual assignment for phone trips only (dispatcher)
- Manual assignment must also respect the queue limit
- Driver notified via FCM on assignment
- Trip status moves: PENDING → ASSIGNED
- `updated_by_user_id` set on assignment
- `declined_count` incremented each time a driver declines

Deliverables:
- Auto-assignment logic tested with priority tiers
- Queue limit enforcement tested (driver with full queue excluded)
- Queued-to-active promotion tested on completion/cancellation
- Google Maps Distance Matrix API integrated
- FCM notification sent on assignment
- Manual dispatcher assignment tested
- Manual assignment rejected when driver queue is full
- `declined_count` incremented correctly on each decline
- Audit fields tested
- Full test suite

---

### Step 11 — Trip Lifecycle Module

Includes the full driver-driven status chain and post-completion ratings, all inside `trip_service.py`.

Endpoints:
```
# Driver actions on their current/queued trip — no IDs in URL
POST   /driver/trip/current/accept       # driver accepts (DRIVER)
POST   /driver/trip/current/decline      # driver declines (DRIVER)
POST   /driver/trip/current/arrive       # driver arrived at pickup (DRIVER)
POST   /driver/trip/current/start        # driver starts trip (DRIVER)
POST   /driver/trip/current/complete     # driver completes trip (DRIVER)

# Driver rates the customer of the most recently completed trip
POST   /driver/trip/last/rate-customer   # driver rates customer (DRIVER)

# Customer rates the driver of the most recently completed trip
POST   /trips/last/rate-driver           # customer rates driver (CUSTOMER)
```

Status chain:
```
ASSIGNED → ACCEPTED → ARRIVED → STARTED → COMPLETED
         ↘ DECLINED (triggers re-assignment)
```

Lifecycle Rules:
- Each status transition is guarded — no skipping steps
- Backend resolves "current trip" from the driver's auth context
- DECLINED triggers auto-assignment retry (ARQ job)
- ACCEPTED triggers FCM to customer: "Your driver is on the way"
- ARRIVED triggers FCM to customer: "Your driver has arrived"
- ARRIVED sets `arrived_at` timestamp — standby timer starts from this field
- STARTED stops the standby charge timer
- COMPLETED triggers FCM to customer: "Your trip is complete"
- `started_at` set on STARTED
- `completed_at` set on COMPLETED
- `updated_by_user_id` set on every transition
- After COMPLETED, the driver's queued trip (if any) becomes their new current trip

Rating Rules:
- Rating endpoint operates on the user's most recently completed trip
- Each party can rate once per trip — duplicate attempts return 409
- Backend determines "last trip" from auth context — no IDs passed
- Rating updates running average on profile
- `driver_profiles.rating` updated when customer rates
- `customer_profiles.rating` updated when driver rates
- Rating logic lives inside `trip_service.py` — no separate `rating_service.py`

Deliverables:
- Full status chain tested
- Guard logic tested (invalid transitions rejected)
- FCM notifications tested at each trigger point
- `arrived_at` timestamp set correctly on ARRIVED
- Standby timer ARQ job tested — starts from `arrived_at`
- Decline → re-assignment flow tested
- Current/queued promotion tested on COMPLETED
- Rating endpoints tested — no IDs accepted in URL
- Running average calculation tested
- Duplicate rating prevention tested
- Audit fields tested
- Full test suite

---

### Step 12 — Trip Cancellation Module

Endpoints:
```
# Customer cancels their current trip — no ID in URL
POST   /trips/current/cancel               # customer cancels their active trip (CUSTOMER)

# Driver cancels their current trip — no ID in URL
POST   /driver/trip/current/cancel         # driver cancels their active trip (DRIVER)

# Dispatcher cancels a PHONE_REQUEST trip — internal panel, uses ID
POST   /trips/{id}/cancel                  # dispatcher cancels PHONE_REQUEST only (DISPATCHER)
```

Rules:
- CUSTOMER and DRIVER can cancel any trip at any stage before COMPLETED
- DISPATCHER can cancel PHONE_REQUEST trips only (any stage before COMPLETED)
- DISPATCHER cancellation on APP_REQUEST trips returns 403
- ADMIN and MANAGER cannot cancel trips
- Trip status moves to CANCELLED
- Backend resolves the trip to cancel from the user's auth context for mobile endpoints
- If driver cancels after ACCEPTED: FCM to customer "Your trip was cancelled"
- If customer cancels after ACCEPTED: FCM to driver "Trip cancelled by customer"
- If dispatcher cancels after ACCEPTED: FCM to both driver and customer
- Standby charge timer stopped if running — accumulated charge discarded, no charge applied
- `updated_by_user_id` set on cancellation (records who cancelled)
- If the driver had a queued trip, it becomes their new current trip

Deliverables:
- Cancellation tested from every status stage for each allowed role
- Mobile endpoints tested — no IDs in URL
- Dispatcher cancellation rejected on APP_REQUEST trips (403)
- FCM notifications tested
- Standby timer cancellation tested — charge correctly discarded
- Queued trip promotion tested
- Audit fields tested
- Full test suite

---

### Step 13 — Fare Override Module

Endpoints:
```
PATCH  /driver/trip/last/fare       # driver overrides fare on their last completed trip (DRIVER)
```

Rules:
- Available only on the driver's most recently completed trip
- Backend resolves the trip from the driver's auth context — no ID passed
- Override window: typically until the next trip starts (enforced in service)
- `final_fare` updated
- `fare_overridden` flag set to true
- `updated_by_user_id` set on override
- Override visible to MANAGER in reports
- No reason required from driver

Deliverables:
- Override tested on the most recently completed trip
- Override rejected on older trips
- Flag correctly set and visible to manager
- Audit fields tested
- Full test suite

---

## PHASE 5 — Real-Time Layer

### Step 14 — Driver Location Tracking

WebSocket:
```
WS  /ws/driver/location             # driver sends location (DRIVER)
```

Rules:
- Driver sends latitude + longitude every few seconds
- Location stored in `driver_locations` table
- Latest location used for assignment distance calculation
- Driver must be authenticated to connect

Deliverables:
- WebSocket connection tested
- Location updates stored correctly
- Unauthenticated connections rejected
- Full test suite

---

### Step 15 — Customer Live Tracking

WebSocket:
```
WS  /ws/trips/current/track        # customer tracks their current accepted trip (CUSTOMER)
```

Pushes to customer:
```
- Driver latitude / longitude
- ETA (Google Maps Routes API)
- Trip status
```

Rules:
- Tracking starts only after driver ACCEPTED
- Backend resolves the customer's current trip from auth context
- Customer sees: driver name, profile picture, vehicle make/model, color, plate
- No internal IDs pushed to customer
- Connection closes on COMPLETED or CANCELLED

Deliverables:
- Live tracking tested end to end
- ETA calculated via Google Maps Routes API
- Customer info payload tested (no internal IDs)
- Connection lifecycle tested
- Full test suite

---

### Step 16 — Dispatcher Live Monitoring

WebSocket:
```
WS  /ws/dispatch/monitor            # dispatcher receives live updates (DISPATCHER, MANAGER)
```

Pushes to dispatcher:
```
- All active trips and their current status
- Driver locations for active trips
- New trip requests
```

Rules:
- DISPATCHER and MANAGER access only
- Updates pushed on any trip status change
- Driver location updates pushed every few seconds for active trips

Deliverables:
- Dispatcher monitor WebSocket tested
- Role access enforced
- Real-time updates tested
- Full test suite

---

## PHASE 6 — Scheduling

### Step 17 — Scheduled Trips Module

Endpoints:
```
# Customer mobile — no IDs
POST   /trips/scheduled                    # customer schedules trip (CUSTOMER)
GET    /trips/scheduled/mine               # customer's scheduled trips (CUSTOMER)
POST   /trips/scheduled/mine/{slot}/cancel # customer cancels their scheduled trip (CUSTOMER)

# Dispatcher internal panel
POST   /trips/phone/scheduled              # dispatcher schedules phone trip (DISPATCHER)
GET    /trips/scheduled                    # list all scheduled trips (DISPATCHER, MANAGER)
POST   /trips/scheduled/{id}/cancel        # dispatcher cancels scheduled trip (DISPATCHER)
```

Background job (ARQ):
```
- Runs every minute
- Finds scheduled trips due within the next window
- Flags them for dispatcher attention
- Sends FCM to dispatcher: "Scheduled trip due soon"
```

Rules:
- Maximum 24 hours in advance
- Customer may have multiple scheduled trips — `{slot}` identifies position in their list (1, 2, 3...)
- Backend resolves the slot to the actual scheduled trip from the customer's auth context
- Dispatcher manually assigns driver when scheduled time arrives
- No automatic assignment for scheduled trips
- Cancellation is soft — sets status to CANCELLED, never deletes
- `created_by_user_id` set on creation
- `updated_by_user_id` set on cancellation

Deliverables:
- Scheduled trip creation tested (customer and dispatcher paths)
- Customer endpoints tested — no IDs in URL
- Cancellation tested — record preserved with CANCELLED status
- ARQ job tested
- FCM to dispatcher tested
- Audit fields tested
- Full test suite

---

## PHASE 7 — Reporting

### Step 18 — Manager Reporting Module

Endpoints:
```
GET   /reports/trips/               # trip summary (MANAGER)
GET   /reports/trips/overrides/     # fare overrides report (MANAGER)
GET   /reports/drivers/             # driver performance (MANAGER)
GET   /reports/revenue/             # revenue summary (MANAGER)
GET   /reports/cancellations/       # cancellation report (MANAGER)
```

Rules:
- All reports filtered by date range
- Fare override report shows original vs final fare and who overrode it
- Audit trail visible in reports (created_by, updated_by)
- No internal IDs in report responses

Deliverables:
- All report endpoints tested
- Date range filtering tested
- Fare override visibility tested
- Audit trail visibility tested
- Full test suite

---

## PHASE 8 — Hardening

### Step 19 — Security and Production Hardening

- Replace CORS wildcard with explicit allowed origins
- Rate limiting on all public endpoints
- Input validation audit across all schemas
- Error response standardization
- Logging and audit trail review
- Environment config review
- Secrets management review
- Database index audit
- Query performance review

---

### Step 20 — Final Integration Testing
Full end-to-end test of every flow.

Flows tested:
```
App trip:       Customer books → auto-assign → accept → arrive → start → complete → rate
Phone trip:     Dispatcher creates → assigns → accept → arrive → start → complete → rate
Cancellation:   Customer cancels at each stage
Cancellation:   Driver cancels at each stage
Fare override:  Driver overrides fare → manager sees it in report with audit trail
Scheduled trip: Customer schedules → ARQ fires → dispatcher assigns
Standby charge: Driver waits 4+ min → timer auto-starts from arrived_at → added to fare
Standby cancel: Trip cancelled while timer running → charge discarded
Soft delete:    User deactivated → cannot log in → records preserved
Audit trail:    Every operational change has created_by / updated_by populated
```

Deliverables:
- All flows pass end to end
- WebSocket flows tested
- FCM notifications verified
- Background jobs verified
- Soft delete verified across all tables
- Audit fields verified across all tables
- System ready for frontend integration

---

## Step Summary

| Phase | Steps | Focus |
|---|---|---|
| 1 — Foundation | 1–4 | Scaffolding, enums, auth, users |
| 2 — Fleet | 5–6 | Vehicles, driver-vehicle assignment |
| 3 — Pricing | 7–8 | Zones, fare matrix, fare engine |
| 4 — Trip Engine | 9–13 | Trip creation, lifecycle + ratings, cancellation, fare override |
| 5 — Real-Time | 14–16 | Location tracking, live tracking, dispatcher monitor |
| 6 — Scheduling | 17 | Scheduled trips |
| 7 — Reporting | 18 | Manager reports |
| 8 — Hardening | 19–20 | Security, production readiness, integration testing |

**Total: 20 Steps**
