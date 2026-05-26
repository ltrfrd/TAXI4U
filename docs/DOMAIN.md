# DOMAIN — Business Logic Reference

This document explains the business rules behind the code. When something in the codebase looks strange, the answer is probably here.

---

## The Taxi Operation

This system serves a single taxi company operating in Cochrane, Alberta. The company:
- Takes ride requests through a mobile customer app
- Takes ride requests by phone (handled by a dispatcher)
- Assigns rides to drivers who use a mobile driver app
- Manages vehicles, drivers, and pricing through web panels

---

## Roles and Responsibilities

### ADMIN
The technical owner of the software. Touches infrastructure, not operations.

### MANAGER
The operational owner of the taxi company. Creates users, manages vehicles, sets pricing, reviews reports. The Manager runs the day-to-day business through the system.

### DISPATCHER
Handles phone-in customers. Creates PHONE_REQUEST trips, picks drivers manually, monitors active trips, contacts drivers and customers when needed. Dispatcher does not cancel APP_REQUEST trips.

### DRIVER
The person behind the wheel. Goes online, accepts trips, drives, gets paid. Uses the mobile driver app.

### CUSTOMER
The rider. Books through the mobile app or by phone. The phone customer is created by the dispatcher; the app customer creates their own account.

---

## The Two Trip Types

### APP_REQUEST
Customer opens the mobile app, sets pickup and dropoff, submits.

System reaction:
1. Trip is created with status `PENDING`
2. Fare is calculated immediately and stored as `suggested_fare`
3. Auto-assignment kicks in (see Driver Assignment below)
4. Customer waits to see "Your driver is on the way"

No dispatcher involvement.

### PHONE_REQUEST
Customer calls the taxi company. A human dispatcher picks up.

Dispatcher reaction:
1. Dispatcher creates the trip in the dispatcher panel
2. Dispatcher manually picks a driver and assigns
3. If declined, dispatcher reassigns to another driver
4. Trip proceeds same as app trip from there

Dispatcher stays involved until the trip starts.

---

## Driver Assignment Logic

Auto-assignment runs for APP_REQUEST trips only.

```
Priority 1 — Nearest ACTIVE online driver with NO active trip and NO queued trip
Priority 2 — Nearest ACTIVE online driver WITH an active trip but NO queued trip
Excluded   — Drivers who already have both an active trip AND a queued trip
```

"Nearest" means road distance from the driver's last known GPS location to the customer's pickup point, computed via the Google Maps Distance Matrix API.

If a driver declines, the system moves to the next nearest driver and tries again. There is no decline limit. There is no timeout. As long as someone with capacity is online, the customer gets a driver.

### Driver Queue Limit
A driver may hold at most **1 active trip + 1 queued trip**. When both slots are full, the driver is excluded from new assignments — both automatic and dispatcher-initiated.

When the active trip completes or is cancelled, the queued trip is promoted to become the new active trip. The driver re-enters the assignment pool.

This limit exists to keep ETAs realistic, simplify dispatch logic, prevent driver overload, and keep the dispatcher's operational view clean.

---

## Fare Calculation

The fare engine runs at trip creation. It produces a `suggested_fare` based on three priority tiers:

### Priority 1 — Special Fixed Route
If pickup is in any of the 26 Cochrane zones and dropoff is Calgary International Airport, the fare is **$90.00 fixed**. This overrides everything.

### Priority 2 — Fare Matrix
If both pickup and dropoff are within the 26 Cochrane zones, the fare is whatever the fare matrix says for that pair. Pricing is symmetrical — the matrix stores each pair once.

### Priority 3 — Outside Zone
If dropoff is outside the 26 zones (and not Calgary Airport), the fare is **$2.00/km** based on road distance. Road distance is stored in `trips.distance_km` at trip creation.

### Additional Fees
- **Stop fee** — $4.00 per stop within a delivery
- **Standby charge** — $0.50/min after the driver has waited 4 minutes at the pickup point. Triggered automatically by a background job, not by the driver.
- **GST** — already baked into all listed prices and the $2/km rate.

### Driver Override
The driver may change the final fare after the trip is complete. No reason is required. The system flags the trip so the manager can see it. This exists because the system can't always know real conditions (long wait, traffic, route changes) — the driver does.

The customer never sees the fare at any stage. Pricing is internal.

---

## The Trip Lifecycle

```
PENDING ─────────────┐
                     ▼
                 ASSIGNED ────────────► DECLINED → re-assign
                     │
                     ▼
                 ACCEPTED ────────────────────────────┐
                     │                                │
                     ▼                                ▼
                  ARRIVED                          CANCELLED
                     │
                     ▼
                  STARTED ──────────────────────── CANCELLED
                     │
                     ▼
                 COMPLETED
```

### PENDING
Trip exists but no driver yet. Auto-assignment runs (app trip) or dispatcher is choosing (phone trip).

### ASSIGNED
Driver has been told about the trip. They haven't responded yet.

### ACCEPTED
Driver accepted. Customer is notified: "Your driver is on the way."

### ARRIVED
Driver is at the pickup point. Customer is notified: "Your driver has arrived."

The standby charge timer starts automatically from the `arrived_at` timestamp if the driver waits more than 4 minutes. The timer is triggered by a background job — the driver does not press anything.

### STARTED
Driver pressed Start. The trip is in progress. The standby charge timer stops.

### COMPLETED
Driver pressed Complete. The trip is over. Customer is notified. Both parties can now rate each other. The driver may override the fare here.

### CANCELLED
The trip was cancelled before completion. Two roles can cancel:
- **Customer** — any trip, any stage before COMPLETED
- **Driver** — any trip, any stage before COMPLETED

ADMIN, MANAGER, and DISPATCHER cannot cancel APP_REQUEST trips. DISPATCHER can cancel PHONE_REQUEST trips only (see below).

When a trip is cancelled:
- If the standby timer was running, the accumulated charge is **discarded** — no charge is applied
- If the driver had a queued trip, it becomes their new current trip
- `updated_by_user_id` records who cancelled

### DISPATCHER CANCELLATION
Dispatcher can cancel **PHONE_REQUEST trips only**, at any stage before COMPLETED. This authority exists because the dispatcher created the trip and manages it end to end. Attempting to cancel an APP_REQUEST trip as a dispatcher returns 403.

Standby discard on cancellation applies the same way — no charge regardless of who cancels.

### DECLINED
The driver declined. The system finds the next nearest driver. Phone trips: the dispatcher reassigns manually.

---

## Cancellation Rules Summary

| Who | Which Trips | Before STARTED | After STARTED | Notes |
|---|---|---|---|---|
| Customer | Any | ✓ | ✓ | Standby charge discarded |
| Driver | Any | ✓ | ✓ | Standby charge discarded |
| Dispatcher | PHONE_REQUEST only | ✓ | ✓ | APP_REQUEST returns 403 |
| Admin | None | ✗ | ✗ | — |
| Manager | None | ✗ | ✗ | — |

> **Open decision:** What happens when a customer changes their mind mid-ride (after STARTED)? Current handling: driver completes the trip at the current location, then uses the fare override to adjust the amount. No mid-trip cancellation logic is implemented. This will be revisited if the real-world operation identifies a better approach.

---

## Real-Time Tracking

### Driver Location
The driver app pushes GPS coordinates every few seconds over a WebSocket. The latest location is stored and used for assignment distance calculation.

### Customer Live Tracking
Starts at `ACCEPTED`, ends at `COMPLETED` or `CANCELLED`. The customer sees:
- Driver's live position on the map
- ETA (Google Maps Routes API)
- Driver name and profile picture
- Vehicle make, model, color, license plate
- Current trip status

No internal IDs ever reach the customer.

### Dispatcher Monitoring
Dispatcher and Manager can monitor all active trips in real time — driver positions, statuses, new requests coming in.

---

## Scheduled Trips

Customers and dispatchers can schedule a trip up to **24 hours** in advance.

A background job runs every minute and flags scheduled trips that are coming due. The dispatcher then assigns a driver manually. There is no automatic assignment for scheduled trips.

---

## Ratings

After `COMPLETED`:
- Customer rates the driver (1–5)
- Driver rates the customer (1–5)

Each party can rate once per trip. The rating updates a running average on the profile (`driver_profiles.rating` or `customer_profiles.rating`). The history of individual ratings is not stored — only the average.

---

## Soft Delete

Nothing is ever hard-deleted. Records become INACTIVE instead.

| Record Type | How |
|---|---|
| Users | `status: INACTIVE` |
| Vehicles | `status: INACTIVE` |
| Zones, fare matrix entries, special routes | `is_active = false` |
| Driver-vehicle assignments | `is_active = false`, plus `unassigned_at` timestamp |

This protects historical trip data and reports.

---

## Audit Trail

Every operational change is attributed to a user.

| Table | Fields |
|---|---|
| trips | `created_by_user_id`, `updated_by_user_id` |
| vehicles | `created_by_user_id`, `updated_by_user_id` |
| zones | `created_by_user_id`, `updated_by_user_id` |
| fare_matrix | `created_by_user_id`, `updated_by_user_id` |
| special_routes | `created_by_user_id`, `updated_by_user_id` |
| users | `updated_by_user_id` |
| driver_vehicle_assignments | `assigned_by_user_id` |

The manager's reports include attribution so accountability is always traceable.

---

## Why Things Are the Way They Are

### Why no fare visibility for customers?
The fare matrix is symmetrical and zone-based, not distance-based. Showing a fare upfront would invite haggling and disputes. The driver controls the final number.

### Why does a driver on a trip get assigned another?
Because in a small fleet, refusing to queue means refusing the customer. The customer always gets a driver. But the queue is capped at 1 — beyond that, ETAs become unrealistic and dispatch logic gets messy.

### Why is the standby timer automatic?
To remove driver friction. Drivers shouldn't have to remember to press a button — the system tracks the wait.

### Why is standby charge discarded on cancellation?
The standby charge compensates the driver for waiting while the trip is still happening. If the trip is cancelled, there is no ride to charge for. The driver's recourse is to note the wait as context, but no charge is applied.

### Why no decline limit?
Because the goal is to serve every request. The system tries until it succeeds.

### Why soft delete everywhere?
Because a deleted user might appear in last month's revenue report. Hard deletes destroy history.

### Why can't dispatcher cancel APP_REQUEST trips?
The dispatcher has no operational relationship to app trips — those are between the customer and the auto-assignment system. Giving dispatchers cancel authority over them would create confusion and accountability gaps.
