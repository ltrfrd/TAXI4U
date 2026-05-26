# RUNBOOK — Operational Issues and Fixes

This is the document you reach for when something is broken in production. Each entry is a real problem, its symptoms, the diagnosis, and the fix.

Entries are added every time a new incident happens. Never delete entries — past incidents often recur.

---

## How to Use This Runbook

1. Find the symptom that matches what you're seeing
2. Run the diagnosis steps to confirm the cause
3. Apply the fix
4. After resolution, update this document if the steps changed

---

## Entry Template

```
## [Short Title]
Severity: Low | Medium | High | Critical
Last seen: YYYY-MM-DD

### Symptoms
What does the user or system see?

### Diagnosis
How do you confirm this is the issue?

### Fix
What to do, step by step.

### Prevention
What to put in place so this doesn't recur?
```

---

## Driver Location Not Updating

Severity: High
Last seen: (initial entry, no incidents yet)

### Symptoms
- Customer live tracking shows a stale driver position
- Dispatcher panel shows driver in the wrong place
- Auto-assignment picks a driver who is actually far away

### Diagnosis
1. Check the driver's WebSocket connection status in the logs
2. Query `driver_locations` for that driver — when was the last update?
3. Check whether the driver's app has GPS permission

### Fix
- If WebSocket disconnected: driver app reconnects automatically. Confirm the reconnection in logs.
- If GPS permission missing: contact the driver to re-grant location permission
- If app crashed: driver restarts the app
- If server-side issue: check WebSocket handler logs for errors

### Prevention
- Driver app shows a banner when location updates stop
- Driver app retries WebSocket connection with exponential backoff
- Manager dashboard flags drivers whose `updated_at` is older than 30 seconds while online

---

## FCM Push Notifications Not Delivered

Severity: High
Last seen: (initial entry)

### Symptoms
- Driver doesn't get "new trip assigned" notification
- Customer doesn't get "driver arrived" notification
- App appears not to know a trip status changed

### Diagnosis
1. Check FCM credentials are valid (Firebase console)
2. Check the user's FCM token is current — old tokens get invalidated
3. Check Firebase quota in the Firebase console
4. Look at backend logs for FCM send errors

### Fix
- Invalid token: prompt the app to refresh and re-register the FCM token
- Quota exceeded: upgrade Firebase plan
- Backend error: check the FCM client code in `app/external/fcm.py`

### Prevention
- App refreshes FCM token on every app startup
- Backend logs all FCM send failures with the user ID
- Alert if FCM error rate exceeds 5%

---

## ARQ Worker Stopped Processing Jobs

Severity: Critical
Last seen: (initial entry)

### Symptoms
- Standby charge timer never triggers
- Scheduled trips never get flagged
- Auto-assignment retries don't fire
- Manager doesn't see notifications for due scheduled trips

### Diagnosis
1. Check if the ARQ worker process is running on the server
2. Check Redis connection from the worker
3. Look at ARQ logs for crashes

### Fix
- Restart the ARQ worker: `systemctl restart taxi-arq-worker` (or your service name)
- If Redis is down: restart Redis, then the worker
- If worker is crashing on startup: check the most recent code change for syntax errors or import failures

### Prevention
- ARQ worker runs as a managed service with auto-restart
- Monitor the worker process — alert if it's not running
- Health endpoint that confirms a recent job ran

---

## Database Connection Pool Exhausted

Severity: Critical
Last seen: (initial entry)

### Symptoms
- API endpoints start timing out
- Logs show "QueuePool limit of size X overflow Y reached"
- WebSocket connections fail

### Diagnosis
1. Check PostgreSQL active connection count
2. Look for long-running queries
3. Check whether a recent code change introduced a connection leak

### Fix
- Restart the FastAPI app to clear the pool
- Kill long-running queries in PostgreSQL
- If recurring: review recent code for missing `db.close()` or context manager misuse

### Prevention
- Use `Depends(get_db)` pattern everywhere
- Set connection pool limits appropriately for the server size
- Add slow query logging

---

## Google Maps API Quota Exceeded

Severity: High
Last seen: (initial entry)

### Symptoms
- Auto-assignment fails (can't calculate distance)
- ETA stops working for customers
- Errors in logs from Distance Matrix or Routes API

### Diagnosis
1. Check Google Cloud Console for quota usage
2. Check billing status

### Fix
- Increase quota in Google Cloud Console
- Or pay overage if billing is enabled
- Temporarily fall back to straight-line distance (NOT for production, only as emergency)

### Prevention
- Set up billing alerts at 50%, 75%, 90% of monthly quota
- Cache Distance Matrix results for repeated queries
- Monitor API usage trend weekly

---

## Driver Assignment Loop Stuck

Severity: High
Last seen: (initial entry)

### Symptoms
- Trip stays in `PENDING` forever
- ARQ logs show assignment job retrying indefinitely
- No drivers online

### Diagnosis
1. Query `driver_profiles` — how many drivers have `is_online = true`?
2. Check `driver_locations` — when were they last updated?
3. Look at the assignment service logs

### Fix
- If no drivers are online: nothing to fix; this is expected. Customer needs to wait.
- If drivers are online but stale: driver app reconnection issue, see "Driver Location Not Updating"
- If logic bug: check the assignment service for an edge case

### Prevention
- Manager dashboard shows current online driver count
- Alert if there are pending trips with no online drivers for more than 5 minutes

---

## Trip Status Stuck

Severity: Medium
Last seen: (initial entry)

### Symptoms
- A trip is stuck in `ARRIVED` for hours
- A trip is stuck in `STARTED` for an unreasonable duration

### Diagnosis
1. Check the trip in the dispatcher panel — what's the status?
2. Contact the driver to confirm what happened
3. Check the driver app logs

### Fix
- Driver forgot to complete: manually contact, ask them to complete
- Driver app crashed mid-trip: manually update status via the database (record who did it and why in `updated_by_user_id` and a note)
- This should be rare — fixing manually is acceptable but document each occurrence

### Prevention
- Driver app reminds about incomplete trips on next login
- Dispatcher dashboard flags trips in non-terminal status for over N hours

---

## Standby Timer Didn't Stop on Trip Start

Severity: Medium
Last seen: (initial entry)

### Symptoms
- Trip has higher standby charge than expected
- Driver complains about wrong fee

### Diagnosis
1. Check the trip's `started_at` timestamp
2. Check the ARQ standby job — when did it fire and stop?
3. Compare against the actual events

### Fix
- Adjust the final fare manually (driver fare override flow)
- Investigate the standby ARQ job logic

### Prevention
- The standby ARQ job must check the trip status on every tick — if not `ARRIVED`, stop
- Add a guard: standby charge cannot exceed N minutes total

---

## Database Migration Failed in Production

Severity: Critical
Last seen: (initial entry)

### Symptoms
- Deployment fails
- Alembic shows the migration in an inconsistent state

### Diagnosis
1. Check the migration logs
2. Query `alembic_version` to see where the chain stopped
3. Read the failed migration's SQL

### Fix
- If migration is reversible: `alembic downgrade -1`, fix, redeploy
- If migration partially applied: hand-fix the database to a clean state, then mark the migration as applied with `alembic stamp <revision>`
- Never edit an already-applied migration file. Create a new one to correct it.

### Prevention
- Test every migration on a staging database first
- Backup the database before any migration
- Migrations are reviewed in PRs by a second engineer

---

## Customer Sees Wrong Vehicle Info

Severity: Medium
Last seen: (initial entry)

### Symptoms
- Customer is told "look for a blue Toyota" but the driver arrives in a red Honda

### Diagnosis
1. Check `driver_vehicle_assignments` — what's the current assignment?
2. Compare against what was shown to the customer
3. Check whether the driver switched vehicles mid-trip without updating the assignment

### Fix
- Manager updates the assignment to reflect reality
- Notify the customer

### Prevention
- Manager assigns vehicles to drivers at shift start
- Driver app prompts to confirm vehicle assignment when going online
- Mid-trip vehicle changes are not allowed in the system (driver completes current trip first)
