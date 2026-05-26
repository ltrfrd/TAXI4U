# TAXI APP — Architecture & System Design Document
*Cochrane, Alberta — May 2026*

---

## 1. Project Overview

A taxi fleet management and ride-request platform built for single-operator use in Cochrane, Alberta. The system handles customer app rides, dispatcher phone-requested rides, driver trip management, fleet monitoring, and Cochrane fare-zone pricing.

| Component | Platform | Users |
|---|---|---|
| Customer App | Mobile | CUSTOMER |
| Driver App | Mobile | DRIVER |
| Dispatcher Panel | Web | DISPATCHER |
| Manager Dashboard | Web | MANAGER |
| Admin Panel | Web | ADMIN |

---

## 2. Project Structure

```
taxi4u-app/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── dependencies.py
│   │   │   ├── enums.py
│   │   │   └── security.py
│   │   │
│   │   ├── constants/
│   │   │   ├── pricing.py
│   │   │   ├── notifications.py
│   │   │   └── timing.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── driver_profile.py
│   │   │   ├── customer_profile.py
│   │   │   ├── vehicle.py
│   │   │   ├── driver_vehicle_assignment.py
│   │   │   ├── zone.py
│   │   │   ├── fare_matrix.py
│   │   │   ├── special_route.py
│   │   │   ├── trip.py
│   │   │   ├── driver_location.py
│   │   │   └── password_reset_token.py
│   │   │
│   │   ├── schemas/
│   │   │   │
│   │   │   ├── internal/
│   │   │   │   ├── user.py
│   │   │   │   ├── vehicle.py
│   │   │   │   ├── trip.py
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── public/
│   │   │       ├── user.py
│   │   │       ├── vehicle.py
│   │   │       ├── trip.py
│   │   │       └── ...
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── vehicle_service.py
│   │   │   ├── assignment_service.py
│   │   │   ├── fare_service.py
│   │   │   ├── trip_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── tracking_service.py
│   │   │   └── report_service.py
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── vehicles.py
│   │   │   ├── assignments.py
│   │   │   ├── fares.py
│   │   │   ├── trips.py
│   │   │   └── reports.py
│   │   │
│   │   ├── background/
│   │   │   ├── worker.py
│   │   │   ├── assignment_jobs.py
│   │   │   ├── standby_jobs.py
│   │   │   ├── scheduled_trip_jobs.py
│   │   │   └── notification_jobs.py
│   │   │
│   │   ├── websockets/
│   │   │   ├── driver_tracking.py
│   │   │   ├── customer_tracking.py
│   │   │   └── dispatcher_monitor.py
│   │   │
│   │   ├── external/
│   │   │   ├── google_maps.py
│   │   │   └── firebase_fcm.py
│   │   │
│   │   ├── seeds/
│   │   │   ├── seed_zones.py
│   │   │   ├── seed_fare_matrix.py
│   │   │   ├── seed_special_routes.py
│   │   │   └── seed_admin.py
│   │   │
│   │   └── utils/
│   │       ├── datetime_utils.py
│   │       ├── validators.py
│   │       └── formatting.py
│   │
│   ├── migrations/
│   │   └── versions/
│   │
│   ├── tests/
│   │   │
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   │
│   │   └── fixtures/
│   │       ├── users.py
│   │       ├── trips.py
│   │       ├── vehicles.py
│   │       └── zones.py
│   │
│   ├── scripts/
│   │   ├── create_admin.py
│   │   ├── reset_dev_db.py
│   │   └── seed_all.py
│   │
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── mobile/
│   │
│   ├── customer/
│   │
│   ├── driver/
│   │
│   └── shared/
│       ├── api/
│       ├── hooks/
│       ├── components/
│       ├── services/
│       └── utils/
│
├── web-panel/
│   │
│   └── src/
│       │
│       ├── routes/
│       │   ├── admin/
│       │   ├── manager/
│       │   └── dispatcher/
│       │
│       ├── api/
│       ├── hooks/
│       ├── store/
│       ├── shared/
│       ├── components/
│       ├── layouts/
│       ├── services/
│       └── utils/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── CONVENTIONS.md
│   ├── DECISIONS.md
│   ├── DOMAIN.md
│   ├── MIGRATIONS.md
│   ├── RUNBOOK.md
│   └── API_EXAMPLES.md
│
├── docker-compose.yml
├── Makefile
├── .gitignore
├── README.md
└── LICENSE
```

---

## 3. User Roles

All users share a single login page. The backend checks role and status, then routes each user to their correct dashboard.

### ADMIN
Platform and software management only. No operational involvement.
- System and technical configuration
- User account management for admin-level accounts only

### MANAGER
Full operational control of the taxi company.
- Create and manage users: dispatchers, drivers, customers
- Create and manage vehicles
- Configure zones and pricing
- Monitor fleet and trips
- Review reports
- Handle complaints and cancellations

### DISPATCHER
Handles phone-requested trips only.
- Create phone trips
- Assign and reassign drivers
- Monitor active trips
- Schedule future trips
- Contact drivers and customers

### DRIVER
Handles trip execution from mobile app.
- Go online / offline
- Accept or decline trips
- Navigate to customer
- Start and complete trips
- Contact customer or dispatcher
- Report incidents

### CUSTOMER
Books rides through the mobile app. Self-registers.
- Create trip requests
- Set pickup and dropoff
- Track driver live
- View ETA, driver name, profile picture, vehicle, license plate
- Cancel trips
- View trip history
- Schedule future trips
- Rate trips

---

## 4. Authentication Architecture

Single login system for all roles. JWT-based with refresh token support.

### Token Strategy

| Token | Duration | Purpose |
|---|---|---|
| Access Token | 30 minutes | Sent with every API request |
| Refresh Token | 30 days | Silently issues new access token |

### Account Status
- `ACTIVE` — can log in and operate
- `INACTIVE` — account disabled, cannot log in

### Rules
- Status checked on every protected request
- Inactive users rejected immediately on any request
- Password reset is self-serve via email

### Endpoints
```
POST  /auth/login
POST  /auth/logout
POST  /auth/refresh
GET   /auth/me
POST  /auth/forgot-password
POST  /auth/reset-password
```

---

## 5. Database Architecture

### users
One table for all roles.
```
id, full_name, phone, email, password_hash,
role, status,
updated_by_user_id,
created_at, updated_at
```

### driver_profiles
```
user_id, profile_picture, is_online, rating, total_trips
```

### customer_profiles
Customers self-register through the mobile app.
```
user_id, rating, total_trips
```

### Internal ID Rule
Database IDs are internal only. Never exposed to customers or drivers. The UI uses names, vehicle information, license plate, trip status, and ETA.

---

## 6. Vehicle Architecture

Managed by MANAGER only.

### vehicles
```
id, plate_number, make, model, year, color,
status,
created_by_user_id, updated_by_user_id,
created_at, updated_at
```

### Vehicle Status
- `ACTIVE`
- `INACTIVE`

---

## 7. Driver ↔ Vehicle Assignment

Drivers and vehicles are not permanently linked. A driver may switch vehicles during the day. A vehicle may be used by different drivers. Manager assigns vehicles to drivers.

### driver_vehicle_assignments
```
id, driver_user_id, vehicle_id,
assigned_by_user_id,
assigned_at, unassigned_at, is_active
```

- One active assignment per driver at a time
- Assignment managed by MANAGER

---

## 8. Zone Architecture

26 defined zones within Cochrane. Pricing is symmetrical — A to B equals B to A. Zones and pricing managed by MANAGER.

### zones
```
id, name,
is_active,
created_by_user_id, updated_by_user_id,
created_at, updated_at
```

### fare_matrix
```
id, pickup_zone_id, dropoff_zone_id,
price,
is_active,
created_by_user_id, updated_by_user_id,
created_at, updated_at
```

### special_routes
```
id, pickup_area, dropoff_area,
fixed_price,
is_active,
created_by_user_id, updated_by_user_id,
created_at, updated_at
```

### Cochrane Zones (26)

| # | Zone Name | # | Zone Name |
|---|---|---|---|
| 1 | Downtown/Quarry | 14 | Fireside (Business Area) |
| 2 | East End/Industrial | 15 | Fireside (Residential) |
| 3 | Riverview/Greystone | 16 | Willows/Rivercrest/Ford |
| 4 | SLS Centre (SLRC) | 17 | Riversong/BVHS |
| 5 | Glenbow | 18 | Riviera/Precedence |
| 6 | West Valley/Mitford | 19 | H.Land/Heritage (Shallow) |
| 7 | West Terrace/Pointe | 20 | H.Land/Heritage (Majority) |
| 8 | Cochrane Heights | 21 | Sunset (Before Sunset Rd) |
| 9 | Sunterra | 22 | Sunset (On/Past Sunset Rd) |
| 10 | GE (Close/EV/Sum/Vista) | 23 | Seminary/Interpipeline |
| 11 | GE (View/Haven/Est Ln) | 24 | Monterra/Coch Lk/Camden |
| 12 | Bow Meadows/Crawford | 25 | Spring Hill RV/Cook Rd |
| 13 | Bow Ridge/Jumping Pound | 26 | Airports (All) |

---

## 9. Pricing Rules

### Fare Priority

| Priority | Condition | Price |
|---|---|---|
| 1 — Special Route | Any Cochrane zone → Calgary International Airport | $90.00 fixed |
| 2 — Fare Matrix | Pickup and dropoff both within 26 Cochrane zones | From fare_matrix table |
| 3 — Outside Zone | Dropoff outside the 26 zones (excl. Calgary Airport) | $2.00 / km |

### Additional Fees

| Fee | Amount | Notes |
|---|---|---|
| Stop fee | $4.00 / stop | Within location / delivery / service |
| Standby charge | $0.50 / min | Auto-applied after 4 min driver wait at pickup |
| GST | Included | Built into all listed prices including $2/km rate |

---

## 10. Fare Rules

- Customers do NOT see pricing before or during the trip
- System calculates suggested fare internally
- Driver can override the final fare — no reason required
- Fare override is flagged in the database for Manager visibility
- Final fare is saved on the trip record

---

## 11. Trip Architecture

### trips
```
id, customer_user_id, driver_user_id, dispatcher_user_id,
pickup_address, dropoff_address,
pickup_zone_id, dropoff_zone_id,
trip_type, status,
suggested_fare, final_fare, fare_overridden,
created_by_user_id, updated_by_user_id,
started_at, completed_at, created_at, updated_at
```

### Trip Types

| Type | Description |
|---|---|
| `APP_REQUEST` | Customer books through mobile app — automatic assignment |
| `PHONE_REQUEST` | Customer calls in — dispatcher creates and assigns |

### Trip Status Flow

| Status | Description |
|---|---|
| `PENDING` | Trip created, awaiting driver assignment |
| `ASSIGNED` | Driver assigned by system or dispatcher |
| `ACCEPTED` | Driver accepted the trip |
| `ARRIVED` | Driver arrived at pickup location |
| `STARTED` | Trip is in progress |
| `COMPLETED` | Trip finished |
| `CANCELLED` | Cancelled by customer or driver |
| `DECLINED` | Driver declined — system finds next driver |

---

## 12. App Request Flow

Customer app rides use automatic driver assignment. Dispatcher is not involved.

- Customer creates trip
- System finds nearest available driver with capacity — see Section 14 for full priority logic
- Trip sent to driver
- If driver declines, system tries the next nearest driver with capacity
- System keeps trying until a driver accepts — no cancellation timeout
- Trip starts → trip completes

> Nearest is calculated by road distance from driver's last known location to customer pickup point.
> A driver may hold up to 1 active trip + 1 queued trip; drivers with both slots full are skipped.

---

## 13. Phone Request Flow

Phone rides are handled entirely by the dispatcher.

- Customer calls in
- Dispatcher creates trip
- Dispatcher manually assigns a driver
- If driver declines, dispatcher manually reassigns to another driver
- Trip starts → trip completes

---

## 14. Automatic Driver Assignment

| Priority | Driver Condition | Notes |
|---|---|---|
| Priority 1 | Online, ACTIVE, no active trip, no queued trip | Always preferred |
| Priority 2 | Online, ACTIVE, has active trip, no queued trip | Used when no Priority 1 driver available |
| Excluded | Has both an active trip AND a queued trip | Skipped until a slot frees up |

### Driver Queue Limit
- A driver may hold at most **1 active trip + 1 queued trip**
- When both slots are full, the driver is excluded from auto-assignment
- On COMPLETED or CANCELLED of the active trip, the queued trip becomes the new active trip
- Driver re-enters the assignment pool when either slot frees

### Assignment Behavior
- Nearest calculated by road distance via Google Maps Distance Matrix API
- System always finds a driver as long as one with capacity exists
- No decline limit, no timeout
- Manual dispatcher assignment also respects the queue limit

---

## 15. Driver Location Tracking

### driver_locations
```
id, driver_user_id, latitude, longitude, updated_at
```

- Driver app sends location update every few seconds
- Continuous while driver is online
- Used for nearest driver calculation and customer live tracking

---

## 16. Customer Live Tracking

Live tracking begins when the driver accepts the trip.

| Info Shown to Customer | Source |
|---|---|
| Driver live location | driver_locations |
| ETA | Calculated from road distance |
| Driver name | users.full_name |
| Driver profile picture | driver_profiles.profile_picture |
| Vehicle make and model | vehicles.make / vehicles.model |
| Vehicle color | vehicles.color |
| License plate | vehicles.plate_number |
| Trip status | trips.status |

> No internal IDs are ever exposed to the customer.

---

## 17. Ratings

- Customer rates driver after trip completion
- Driver rates customer after trip completion
- Rating stored as running average on each profile

```
driver_profiles.rating
customer_profiles.rating
```

---

## 18. Notifications

| Recipient | Trigger | Message |
|---|---|---|
| Driver | New trip assigned | You have a new trip request |
| Driver | Trip cancelled by customer | Trip has been cancelled by the customer |
| Customer | Driver accepted trip | Your driver is on the way |
| Customer | Driver has arrived | Your driver has arrived at pickup |
| Customer | Trip completed | Your trip is complete |

---

## 19. Scheduled Trips

- Available to both customers and dispatchers
- Maximum scheduling window: 24 hours in advance
- Dispatcher manually assigns driver when the scheduled time arrives
- No automatic assignment for scheduled trips

---

## 20. Trip Cancellation

| Who | Which Trips | When | Notes |
|---|---|---|---|
| Customer | Any | Any stage before completion | No restriction on timing |
| Driver | Any | Any stage before completion | No restriction on timing |
| Dispatcher | PHONE_REQUEST only | Any stage before completion | Dispatcher created it, dispatcher can cancel it |

- ADMIN and MANAGER cannot cancel trips
- APP_REQUEST trips cannot be cancelled by anyone except the customer or driver

---

## 21. Standby Charge

- System automatically starts $0.50/min timer after driver has been waiting 4 minutes at pickup
- Driver does not trigger it manually — fully automatic
- Added on top of the base trip fare
- Timer stops when the trip starts

---

## 22. Soft Delete Strategy

Nothing gets hard-deleted. Ever.

| Table | Strategy |
|---|---|
| users | `status: ACTIVE / INACTIVE` |
| vehicles | `status: ACTIVE / INACTIVE` |
| zones | `is_active` flag |
| fare_matrix | `is_active` flag |
| special_routes | `is_active` flag |
| driver_vehicle_assignments | `is_active` flag |

---

## 23. Audit Fields

Full accountability trail on all operational records.

| Table | Fields |
|---|---|
| trips | `created_by_user_id, updated_by_user_id` |
| vehicles | `created_by_user_id, updated_by_user_id` |
| zones | `created_by_user_id, updated_by_user_id` |
| fare_matrix | `created_by_user_id, updated_by_user_id` |
| special_routes | `created_by_user_id, updated_by_user_id` |
| users | `updated_by_user_id` |
| driver_vehicle_assignments | `assigned_by_user_id` |
