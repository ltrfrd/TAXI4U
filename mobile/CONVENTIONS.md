# CONVENTIONS — Coding Standards

This document defines the rules every file in this codebase must follow. Consistency is more valuable than personal preference.

---

## Project Structure

```
app/
  core/             # framework-level building blocks
    config.py       # environment + settings
    enums.py        # ALL enums centralized
    security.py     # password hashing, JWT
    database.py     # DB session, base model
    dependencies.py # FastAPI dependencies (auth, role checks)
  models/           # SQLAlchemy models
  schemas/          # Pydantic schemas
    internal/       # full internal data (with IDs)
    public/         # what we send to clients (no internal IDs)
  services/         # ALL business logic lives here
  routers/          # HTTP transport only — no business logic
  background/       # ARQ job definitions
  websockets/       # WebSocket handlers
  external/         # Google Maps, FCM clients
migrations/         # Alembic chain — never edit applied migrations
tests/
  unit/             # service-level tests
  integration/      # endpoint-level tests
  e2e/              # full flow tests
```

### Python Package Initialization

Every folder under `app/` MUST contain an `__init__.py` file. This includes:

```
app/__init__.py
app/core/__init__.py
app/constants/__init__.py
app/models/__init__.py
app/schemas/__init__.py
app/schemas/internal/__init__.py
app/schemas/public/__init__.py
app/services/__init__.py
app/routers/__init__.py
app/background/__init__.py
app/websockets/__init__.py
app/external/__init__.py
app/seeds/__init__.py
app/utils/__init__.py
```

- Empty `__init__.py` is acceptable
- Use `__init__.py` to re-export commonly used items only when it improves clarity
- Never use `__init__.py` to run side-effecting code at import time

---

## The Three Hard Rules

### Rule 1 — Services Own Business Logic
Routers do HTTP. Services do logic. No exceptions.

Routers should:
- Parse the request
- Call the service
- Map the result to a response

Routers should NOT:
- Query the database directly
- Run validation beyond Pydantic
- Make permission decisions
- Call other services

### Rule 2 — Enums Are Centralized
Every enum lives in `core/enums.py`. Never inline. Never per-module.

```python
# ✓ Correct
from app.core.enums import TripStatus

# ✗ Wrong — never inline
class TripStatus(str, Enum):
    PENDING = "PENDING"
```

### Rule 3 — Internal IDs Never Leave the Backend
Public schemas use names, plates, and statuses. Internal IDs only appear in:
- Internal schemas
- Service code
- Manager/Dispatcher/Admin tools

If a customer or driver sees an integer ID in their app, that's a bug.

---

## Naming Conventions

### Files
- `snake_case` for everything
- Singular nouns for models: `trip.py`, not `trips.py`
- Plural for routers: `trips.py`, since they manage the resource

### Classes
- `PascalCase` for classes, models, schemas, enums
- Models match the table name in singular: `User`, `Trip`, `Vehicle`

### Functions
- `snake_case` for all functions
- Service functions are descriptive: `create_app_trip()`, not `create()`
- Verb-first: `assign_driver_to_trip()`, not `driver_trip_assignment()`

### Variables
- `snake_case`
- Foreign keys: `customer_user_id`, never just `customer_id` (avoids ambiguity)

---

## Database Conventions

### Table Names
- Plural and lowercase: `users`, `trips`, `driver_profiles`

### Primary Keys
- Always `id`, never `user_id` or similar

### Foreign Keys
- Format: `{role}_user_id` when referring to users:
  - `customer_user_id`
  - `driver_user_id`
  - `dispatcher_user_id`
  - `created_by_user_id`
  - `updated_by_user_id`

### Timestamps
- `created_at` and `updated_at` on every table
- Use UTC always, store as `timestamptz`

### Status Fields
- Use enum types, not free strings
- ACTIVE/INACTIVE for soft delete on users and vehicles
- `is_active` boolean for soft delete on configuration tables

---

## API Conventions

### URL Structure
- Resources are plural: `/trips/`, `/vehicles/`, `/users/`
- Actions on a resource: `POST /trips/{id}/accept`
- Nested only when ownership is clear: `/assignments/driver/{driver_id}`
- No trailing slash on action endpoints

### Internal Panels vs Mobile Endpoints

The system has two endpoint families with very different rules.

**Mobile endpoints (CUSTOMER, DRIVER) — never carry an ID:**

The user's authenticated context resolves what they're acting on. There is no `{id}` in the URL, query string, or response body.

```
# Customer
POST  /auth/register
GET   /auth/me
POST  /trips/app
GET   /trips/current
GET   /trips/history
POST  /trips/current/cancel
POST  /trips/last/rate-driver
POST  /trips/scheduled
GET   /trips/scheduled/mine
POST  /trips/scheduled/mine/{slot}/cancel    # {slot} is a position, not an ID

# Driver
GET   /driver/trip/current
GET   /driver/trip/queued
GET   /driver/history
POST  /driver/trip/current/accept
POST  /driver/trip/current/decline
POST  /driver/trip/current/arrive
POST  /driver/trip/current/start
POST  /driver/trip/current/complete
POST  /driver/trip/current/cancel
POST  /driver/trip/last/rate-customer
PATCH /driver/trip/last/fare
```

**Internal panel endpoints (ADMIN, MANAGER, DISPATCHER) — `{id}` in URLs is fine:**

These users are operators. They need to identify specific records. The UI displays names/plates/timestamps to the human, but the URL layer uses IDs.

```
GET   /users/{id}
PATCH /users/{id}/status
GET   /vehicles/{id}
PATCH /vehicles/{id}/status
GET   /trips/{id}
POST  /trips/{id}/assign
POST  /trips/{id}/reassign
POST  /trips/{id}/cancel              # PHONE_REQUEST only, DISPATCHER
POST  /trips/scheduled/{id}/cancel    # DISPATCHER
POST  /assignments/{id}/unassign
PATCH /zones/{id}/status
PATCH /fares/matrix/{id}/status
PATCH /fares/special-routes/{id}/status
```

**The IDs in internal URLs are not displayed in the UI.** Operators see "Trip from Maria Lopez to 14 Riverview Dr at 2:30 PM," not "Trip #1247."

### HTTP Methods
- `POST` — create or trigger action
- `GET` — read
- `PATCH` — partial update
- `PUT` — full replacement (rarely used)
- `DELETE` — **never used.** All removals are soft-cancels with explicit endpoints.

### Status Codes
- `200` — success with body
- `201` — created
- `204` — success, no body
- `400` — bad request (validation)
- `401` — not authenticated
- `403` — authenticated but not authorized
- `404` — not found
- `409` — conflict (duplicate, invalid state transition)
- `422` — Pydantic validation error (auto)
- `500` — server error

### Error Response Format
Standardized across all endpoints:
```json
{
  "error": "VALIDATION_FAILED",
  "message": "Pickup zone is required",
  "details": {}
}
```

---

## Schema Conventions

### Two Schemas Per Resource

```python
# schemas/internal/trip.py — full data, has IDs
class TripInternal(BaseModel):
    id: int
    customer_user_id: int
    driver_user_id: int | None
    # ...

# schemas/public/trip.py — what clients see
class TripPublic(BaseModel):
    pickup_address: str
    status: TripStatus
    driver_name: str | None
    vehicle_plate: str | None
    # NO internal IDs
```

### Mapping Between Them
Always explicit. Use service-layer functions, not magic.

```python
def to_public(trip: TripInternal) -> TripPublic:
    return TripPublic(
        pickup_address=trip.pickup_address,
        status=trip.status,
        driver_name=trip.driver.full_name if trip.driver else None,
        vehicle_plate=trip.vehicle.plate_number if trip.vehicle else None,
    )
```

---

## Service Conventions

### One Service Function Per Operation
No shared "helper" functions across services. If two services need the same thing, the logic moves up to a dedicated service.

```python
# ✓ Correct — named, single-purpose
def create_app_trip(...): ...
def create_phone_trip(...): ...

# ✗ Wrong — generic
def create_trip(trip_type, ...): ...
```

### Services Receive the Acting User
For audit fields and permission checks:

```python
def create_vehicle(
    payload: VehicleCreate,
    acting_user: User,
    db: Session,
) -> Vehicle:
    # ...
```

### Services Return Internal Schemas
Routers map them to public schemas before responding.

---

## Background Job Conventions (ARQ)

ARQ jobs run asynchronously via Redis. They handle work that cannot happen inside a request/response cycle — timers, retries, periodic checks.

### Job File Organization
Jobs are grouped by domain into separate files under `app/background/`:

```
app/background/
  worker.py              # WorkerSettings — registers all jobs
  assignment_jobs.py     # auto-assignment retry
  standby_jobs.py        # standby charge timer
  scheduled_trip_jobs.py # scheduled trip flagging
```

### Naming
Job functions follow the same verb-first convention as services:

```python
# ✓ Correct
async def retry_auto_assignment(ctx, trip_id: int): ...
async def tick_standby_charge(ctx, trip_id: int): ...
async def flag_scheduled_trips(ctx): ...

# ✗ Wrong
async def assignment_retry(ctx, trip_id: int): ...
async def standby(ctx): ...
```

### Database Access
Jobs create their own database session using the same `get_db` pattern as routers. Never pass a DB session into a job from outside.

```python
# ✓ Correct
async def retry_auto_assignment(ctx, trip_id: int):
    async with get_db() as db:
        await assignment_service.retry_assignment(trip_id, db)

# ✗ Wrong — session passed from outside
async def retry_auto_assignment(ctx, trip_id: int, db: Session): ...
```

### Retry Policy
No retry by default. Opt-in per job only when the consequence of failure justifies it.

| Job | Retry | Reason |
|---|---|---|
| `retry_auto_assignment` | Yes — 3 attempts, 5s delay | Failed assignment leaves customer stuck in PENDING |
| `tick_standby_charge` | No | Next minute's tick covers it; retrying risks double-charging |
| `flag_scheduled_trips` | No | Next minute's run covers it |

To enable retries on a job, set `max_tries` in the job definition:

```python
# ✓ Only for jobs that opt in
class WorkerSettings:
    functions = [
        func(retry_auto_assignment, max_tries=3),
        func(tick_standby_charge),       # no retry
        func(flag_scheduled_trips),      # no retry
    ]
```

### Jobs Are Not Services
Jobs orchestrate — they call services. Business logic lives in the service layer, not inside job functions.

```python
# ✓ Correct — job calls service
async def tick_standby_charge(ctx, trip_id: int):
    async with get_db() as db:
        await trip_service.apply_standby_tick(trip_id, db)

# ✗ Wrong — job contains business logic
async def tick_standby_charge(ctx, trip_id: int):
    async with get_db() as db:
        trip = db.query(Trip).get(trip_id)
        if trip.status == TripStatus.ARRIVED:
            trip.standby_minutes += 1
            db.commit()
```

---

## Error Handling

### Service Layer
Raise typed domain exceptions:

```python
class TripNotFound(Exception): ...
class InvalidStatusTransition(Exception): ...
class DriverAlreadyAssigned(Exception): ...
```

### Router Layer
Catch domain exceptions and map to HTTP:

```python
@router.post("/trips/{id}/accept")
def accept_trip(id: int, ...):
    try:
        return service.accept_trip(id, ...)
    except TripNotFound:
        raise HTTPException(404, "Trip not found")
    except InvalidStatusTransition:
        raise HTTPException(409, "Cannot accept in current status")
```

No business logic in `except` blocks.

---

## Testing Conventions

### Test File Mirrors Source
```
app/services/trip_service.py → tests/unit/services/test_trip_service.py
app/routers/trips.py         → tests/integration/test_trips_endpoints.py
```

### Test Names Are Sentences
```python
def test_create_app_trip_triggers_auto_assignment():
def test_driver_cannot_accept_already_accepted_trip():
def test_fare_override_sets_overridden_flag():
```

### Every New Feature Needs Tests
No PR is merged without tests covering:
- Happy path
- Permission/role enforcement
- Edge cases identified during design

---

## Commits and Branches

### Branch Names
- `feature/step-04-user-management`
- `fix/standby-timer-cancellation`
- `refactor/extract-fare-engine`

### Commit Messages
Format: `[Step XX] Verb in present tense, what changed`

Examples:
```
[Step 03] Add JWT refresh token endpoint
[Step 08] Add Calgary Airport special route to fare engine
[Step 11] Guard ACCEPTED → STARTED transition
```

### Push to GitHub Only at Step Completion
No half-finished steps on master. Use feature branches until a step is done and tested.
