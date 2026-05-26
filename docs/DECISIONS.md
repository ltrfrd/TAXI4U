# DECISIONS — Architecture Decision Records

This document captures every significant architectural decision made for the Taxi App, why it was made, and what alternatives were rejected.

Every new ADR is appended. Past decisions are never deleted — if a decision is reversed, the new ADR references the old one.

---

## ADR Template

```
## ADR-XXX — [Title]
Date: YYYY-MM-DD
Status: Accepted | Rejected | Superseded by ADR-YYY

### Context
What problem are we solving?

### Decision
What did we choose?

### Alternatives Considered
What did we reject, and why?

### Consequences
What does this commit us to? What becomes harder?
```

---

## ADR-001 — Single Login System for All Roles
Date: 2026-05-21
Status: Accepted

### Context
The system has five user types: Admin, Manager, Dispatcher, Driver, Customer. Each needs to authenticate.

### Decision
One login endpoint (`POST /auth/login`) for all roles. Backend reads the user's role from the database and the client routes to the correct dashboard.

### Alternatives Considered
- **Separate login per role** — rejected. Multiplies auth code, complicates password resets, makes future role additions painful.
- **Subdomain per role** — rejected. Operational overhead for no functional gain.

### Consequences
- Single auth codebase to maintain
- Role-based routing happens at the client level
- Adding a new role only requires a new dashboard, not new auth

---

## ADR-002 — JWT with Refresh Token Strategy
Date: 2026-05-21
Status: Accepted

### Context
Mobile drivers stay online all day. Mobile customers may stay logged in for weeks. We need long-lived sessions without sacrificing security.

### Decision
Short-lived access token (30 min) + long-lived refresh token (30 days). Status checked on every protected request so deactivated accounts are rejected mid-session.

### Alternatives Considered
- **Session-based auth** — rejected. Doesn't scale cleanly to mobile, requires sticky sessions, complicates WebSocket auth.
- **Long-lived access tokens** — rejected. Security risk if a token is leaked.

### Consequences
- Two-token logic in clients
- Token refresh must be silent
- INACTIVE status must be checked on every request, not just login

---

## ADR-003 — No Hard Deletes (Soft Delete Strategy)
Date: 2026-05-21
Status: Accepted

### Context
A deleted user might have hundreds of historical trips. A deleted vehicle might appear in financial reports. Hard deletes break referential integrity and destroy audit trails.

### Decision
Nothing is hard-deleted. Users and vehicles use `status: ACTIVE / INACTIVE`. Zones, fare matrix entries, special routes, and driver-vehicle assignments use `is_active` boolean flags.

### Alternatives Considered
- **Hard delete with cascade** — rejected. Destroys reports, breaks foreign keys.
- **Soft delete with timestamp only** — rejected. Less explicit than a status field; harder to query.

### Consequences
- Every list endpoint defaults to filtering out inactive records
- Reports can still show historical data even if user was deactivated
- Database grows monotonically — needs periodic archival strategy later

---

## ADR-004 — Audit Fields on Operational Tables
Date: 2026-05-21
Status: Accepted

### Context
When something goes wrong in operations — wrong fare, mistaken assignment, surprise deactivation — the manager needs to know who did what.

### Decision
Add `created_by_user_id` and `updated_by_user_id` to all operational tables: trips, vehicles, zones, fare_matrix, special_routes. Users get `updated_by_user_id`. Driver-vehicle assignments get `assigned_by_user_id`.

### Alternatives Considered
- **Separate audit log table** — deferred. More flexible, but heavier to implement now. Can be added later for finer-grained tracking.
- **No audit fields** — rejected. Accountability is critical for a taxi operation.

### Consequences
- Every service that creates or updates a record must pass the acting user's ID
- Manager reports can include attribution
- Slight schema overhead per table

---

## ADR-005 — Internal IDs Never Exposed
Date: 2026-05-21
Status: Accepted

### Context
Database integer IDs leak information about scale and can be enumerated. Customers and drivers should never see them.

### Decision
Public-facing responses use names, vehicle info, license plate, and status. Internal IDs are only used in backend logic and admin/manager/dispatcher tools.

### Alternatives Considered
- **UUIDs as public IDs** — partially considered. May still be needed for trip references in URLs. Decision deferred to per-endpoint review.
- **Expose integer IDs** — rejected. Enumeration risk, leaks scale data.

### Consequences
- Two schema layers per resource: internal (full) and public (filtered)
- More mapping code
- Stronger security posture by default

---

## ADR-006 — Symmetrical Fare Matrix
Date: 2026-05-21
Status: Accepted

### Context
26 zones means 676 possible directional pairs. The Cochrane fare chart treats A→B and B→A identically.

### Decision
Store each pair only once. Lookup logic checks both orderings. Total stored pairs: 325.

### Alternatives Considered
- **Store both directions** — rejected. Doubles storage, risks divergence between A→B and B→A prices.

### Consequences
- Fare lookup must always try both (pickup, dropoff) and (dropoff, pickup)
- Admin UI must enforce symmetry on creation
- Cleaner data, smaller table

---

## ADR-007 — Fare Override Without Mandatory Reason
Date: 2026-05-21
Status: Accepted

### Context
The system calculates a suggested fare, but the driver knows real conditions (long wait, multiple stops, traffic). The app exists to ensure drivers are paid fairly.

### Decision
Driver can override final fare with no required reason. Override is flagged in the database so Manager can review patterns.

### Alternatives Considered
- **No override allowed** — rejected. Conflicts with the core goal of fair pay.
- **Require reason for every override** — rejected. Adds friction for drivers; reasons would likely be junk text.

### Consequences
- Manager must monitor override patterns through reports
- Trust placed in drivers; outliers caught in review

---

## ADR-008 — Auto-Assignment Never Gives Up
Date: 2026-05-21
Status: Accepted

### Context
If no driver is available, the system could cancel the trip or queue it. Neither serves the customer well.

### Decision
System always finds a driver as long as anyone is online. Priority 1 is available drivers, Priority 2 is drivers already on a trip. No decline limit, no timeout.

### Alternatives Considered
- **Cancel after N declines** — rejected. Worse customer experience.
- **Queue and retry** — rejected. Same as current behavior but with delay.

### Consequences
- A driver on an active trip may queue another trip
- Driver app must handle "next trip" UX
- Customer always gets a driver if any are online

---

## ADR-009 — Tech Stack Locked
Date: 2026-05-21
Status: Accepted

### Context
Need a stack that is production-grade, maintainable, and scalable for a single-operator taxi app.

### Decision
- Backend: **FastAPI + PostgreSQL**
- Real-time: **FastAPI WebSockets**
- Maps: **Google Maps API** (Distance Matrix + Routes)
- Push notifications: **Firebase FCM**
- Background jobs: **ARQ + Redis**

### Alternatives Considered
- **Django** — rejected. Heavier than needed, ORM less flexible for this workload.
- **Celery instead of ARQ** — rejected. ARQ is async-native and lighter for FastAPI.
- **Mapbox instead of Google Maps** — rejected. Google has better Canadian road coverage including Cochrane.
- **Self-hosted push** — rejected. FCM is free and battle-tested.

### Consequences
- All five components must be available in production
- Single language (Python) across backend and workers
- Costs: Google Maps API usage and Firebase free tier limits

---

## ADR-010 — Rating Logic Lives in Trip Service
Date: 2026-05-21
Status: Accepted

### Context
Ratings are tied directly to trip completion. They update a running average on the user profile and have no history table.

### Decision
No separate `rating_service.py` or `routers/ratings.py`. Rating endpoints (`POST /trips/{id}/rate/driver`, `POST /trips/{id}/rate/customer`) live in the trip router and call `trip_service.py`.

### Alternatives Considered
- **Standalone rating service** — rejected. Rating is a single field update tightly coupled to trip completion. A dedicated service would be a thin wrapper with no real cohesion of its own.
- **Rating history table with separate service** — rejected at design time. Running averages on profiles are sufficient.

### Consequences
- `trip_service.py` owns rating logic
- Step 11 of the roadmap covers both lifecycle and ratings
- If rating history is ever needed, this decision will be revisited

---

## ADR-011 — Customer/Driver Endpoints Use Semantic Routes
Date: 2026-05-21
Status: Accepted

### Context
ADR-005 said internal IDs are never exposed to customers and drivers. But the roadmap still used `{id}` in customer-facing endpoints, which would expose enumerable integers.

### Decision
Split endpoint conventions:
- **Customer/driver mobile endpoints** — semantic routes like `/trips/current`, `/trips/history`, `/auth/me`
- **Internal panel endpoints (ADMIN, MANAGER, DISPATCHER)** — keep `{id}` since these users are operational

If a trip ID must travel through a customer or driver client (e.g. for rating, cancelling), it must be an opaque identifier (UUID or short code), never a sequential integer.

### Alternatives Considered
- **Use integer IDs everywhere** — rejected. Violates ADR-005.
- **Use UUIDs everywhere** — partially accepted. Internal panels can still use integers since they're already trusted users. Customer/driver-facing IDs must be opaque.

### Consequences
- Two endpoint styles in the codebase, by audience
- Customer/driver routes need explicit semantic design
- Slightly more router code, much stronger security posture

---

## ADR-012 — Unassignment Is a State Change, Not a Delete
Date: 2026-05-21
Status: Accepted

### Context
The roadmap originally had `DELETE /assignments/{id}` for ending a driver-vehicle assignment. This contradicts ADR-003 (no hard deletes).

### Decision
Replace with `POST /assignments/{id}/unassign`. The endpoint sets `is_active = false` and `unassigned_at = now()`. The assignment row is preserved for history.

### Alternatives Considered
- **`DELETE /assignments/{id}` with soft-delete semantics** — rejected. HTTP DELETE implies removal; mismatched semantics confuse API consumers.
- **`PATCH /assignments/{id}` with status field** — rejected. Less explicit about the operation.

### Consequences
- All assignment closures preserve history
- Aligns with soft delete philosophy across the system
- API verbs match real behavior

---

## ADR-013 — Dispatcher Can Cancel Phone Trips
Date: 2026-05-21
Status: Accepted, supersedes part of original Trip Cancellation rules

### Context
Original cancellation rule: only CUSTOMER and DRIVER can cancel. But dispatcher operationally manages PHONE_REQUEST trips end to end. Without cancellation authority, support deadlocks emerge (driver unreachable, customer changed mind, etc.).

### Decision
Cancellation authority:
- **CUSTOMER** — any trip, any stage before completion
- **DRIVER** — any trip, any stage before completion
- **DISPATCHER** — PHONE_REQUEST trips only, any stage before completion
- **ADMIN, MANAGER** — cannot cancel

### Alternatives Considered
- **Dispatcher can cancel any trip** — rejected. APP_REQUEST trips are between customer and driver; dispatcher has no operational relationship to them.
- **Manager has cancellation authority** — rejected. Manager is analytical, not operational.

### Consequences
- Dispatcher gets a cancel button on PHONE_REQUEST trips only
- Cancellation rule is tied to trip_type, not just role
- Audit trail records who cancelled and why (via `updated_by_user_id`)

---

## ADR-014 — Every Python Folder Has `__init__.py`
Date: 2026-05-21
Status: Accepted

### Context
Implicit namespace packages (PEP 420) work but cause subtle issues with imports, IDE support, and test discovery. Better to be explicit.

### Decision
Every folder under `app/` contains an `__init__.py` file. Empty is acceptable.

### Alternatives Considered
- **Implicit namespace packages** — rejected. Less predictable, especially with monkey patching or test discovery.

### Consequences
- Slightly more files in the repo
- Cleaner imports
- IDE and pytest behave predictably

---

## ADR-015 — No Public Trip IDs, Ever
Date: 2026-05-21
Status: Accepted, supersedes the deferred UUID note in ADR-005

### Context
ADR-011 considered using opaque public IDs (UUIDs) for customer/driver endpoints. Closer review showed this still leaks an identifier into the client surface. A simpler model avoids the problem entirely.

### Decision
- No `trip_public_id` column
- No UUIDs in customer or driver URLs
- Customer and driver clients operate on session-based concepts:
  - `current trip` — the one active trip the user has right now
  - `last trip` — the most recently completed trip (for rating, fare override)
  - `history` — paginated past trips for display
- Backend resolves the trip from the user's auth context

Internal panel URLs may still use integer `{id}`, but the UI never displays the ID — operators see names, plates, timestamps.

### Alternatives Considered
- **UUID public IDs** (ADR-011 alternative) — rejected. Still leaks an opaque token; mobile app must store and pass it. Session-based resolution is simpler.
- **Short codes** — rejected. Same problem as UUIDs but shorter.

### Consequences
- Mobile endpoints are highly semantic (`/trips/current/cancel`, `/driver/trip/last/fare`)
- A customer can have at most one trip in `current` at a time
- A driver can have at most one trip in `current` and one in `queued`
- Backend must reliably resolve "current" and "last" from auth context
- Customers and drivers never see, store, or transmit any trip identifier

---

## ADR-016 — Driver Queue Limit: 1 Active + 1 Queued
Date: 2026-05-21
Status: Accepted

### Context
ADR-008 said the system never gives up — drivers on active trips can still receive new assignments. Without a limit, drivers could stack arbitrary numbers of queued trips, making ETAs unreliable and dispatch logic complex.

### Decision
A driver may hold at most:
- 1 active trip
- 1 queued trip

When both slots are full, the driver is excluded from auto-assignment AND from manual dispatcher assignment. On COMPLETED or CANCELLED of the active trip, the queued trip becomes the new active trip.

### Alternatives Considered
- **Unlimited queue** — rejected. ETAs become unrealistic; dispatch UX degrades.
- **No queue (1 trip max)** — rejected. Small-fleet scenarios where every driver is busy would mean turning customers away.
- **Queue = 2** — rejected. Marginal benefit, doubles the ETA prediction problem.

### Consequences
- Auto-assignment logic must check both slots
- Manual dispatcher assignment must also enforce the limit
- The driver app handles "current" and "next" trip UX
- When all online drivers have full queues, new trips stay PENDING until capacity opens
- Manager dashboard can show "no available capacity" as a real, monitorable state

---

## ADR-017 — No DELETE Endpoints (Universal Soft-Cancel)
Date: 2026-05-21
Status: Accepted, extends ADR-003 and ADR-012

### Context
ADR-003 established no hard deletes. ADR-012 changed assignment unassignment to a state change. Scheduled trip cancellation was still using `DELETE /trips/scheduled/{id}` — inconsistent.

### Decision
No HTTP `DELETE` verb is used anywhere in this system. Every "removal" is a soft-cancel that preserves the record:
- Scheduled trip cancellation: `POST /trips/scheduled/{id}/cancel`
- Driver-vehicle unassignment: `POST /assignments/{id}/unassign`
- User deactivation: `PATCH /users/{id}/status`
- Vehicle deactivation: `PATCH /vehicles/{id}/status`
- Zone / fare / special route deactivation: `PATCH .../status`

### Consequences
- Universal soft-delete philosophy is now enforced at the API level
- All historical data preserved indefinitely
- No accidental data loss possible through normal API use
- Future archival strategy can selectively purge old records if needed
