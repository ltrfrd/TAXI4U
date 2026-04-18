"""
Focused tests for ride assignment (manual and auto).
Uses an isolated in-memory SQLite DB via StaticPool so setup
sessions and the TestClient share the same connection.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models.driver import Driver
from models.driver_location import DriverLocation
from models.ride_request import RideRequest
from utils.auth import hash_password
from utils.assignment import _dist

# ── in-memory test database ───────────────────────────────────────────────────

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


# ── data helpers ──────────────────────────────────────────────────────────────

def _driver(email, lat, lon, *, status="available", is_active=True):
    """Create a driver + location row and return the Driver id."""
    db = _Session()
    try:
        d = Driver(
            name="Test",
            email=email,
            phone=None,
            password_hash=hash_password("x"),
            is_active=is_active,
            status=status,
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        db.add(DriverLocation(driver_id=d.id, latitude=lat, longitude=lon))
        db.commit()
        return d.id
    finally:
        db.close()


def _driver_no_location(email):
    """Create a driver without a DriverLocation row."""
    db = _Session()
    try:
        d = Driver(
            name="No-loc",
            email=email,
            phone=None,
            password_hash=hash_password("x"),
            is_active=True,
            status="available",
        )
        db.add(d)
        db.commit()
        return d.id
    finally:
        db.close()


def _ride(pickup_lat=None, pickup_lon=None, status="pending"):
    """Create a ride request and return its id."""
    db = _Session()
    try:
        r = RideRequest(
            pickup_text="A",
            dropoff_text="B",
            pickup_lat=pickup_lat,
            pickup_lon=pickup_lon,
            status=status,
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return r.id
    finally:
        db.close()


# ── unit: _dist ───────────────────────────────────────────────────────────────

def test_dist_known_value():
    assert _dist(0, 0, 3, 4) == 25  # 3² + 4²

def test_dist_same_point():
    assert _dist(5.0, 5.0, 5.0, 5.0) == 0

def test_dist_ordering():
    near = _dist(51.04, -114.0, 51.05, -114.0)
    far  = _dist(51.04, -114.0, 51.90, -114.0)
    assert near < far


# ── manual assign: contract unchanged ────────────────────────────────────────

def test_manual_assign_success():
    _driver("d@t.com", 51.0, -114.0)
    ride_id = _ride()

    r = client.post(f"/rides/{ride_id}/assign", json={"driver_email": "d@t.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "assigned"
    assert body["assigned_driver"]["email"] == "d@t.com"
    assert body["assigned_at"] is not None


def test_manual_assign_inactive_driver_rejected():
    _driver("d@t.com", 51.0, -114.0, is_active=False)
    ride_id = _ride()

    r = client.post(f"/rides/{ride_id}/assign", json={"driver_email": "d@t.com"})
    assert r.status_code == 400


def test_manual_assign_offline_driver_rejected():
    _driver("d@t.com", 51.0, -114.0, status="offline")
    ride_id = _ride()

    r = client.post(f"/rides/{ride_id}/assign", json={"driver_email": "d@t.com"})
    assert r.status_code == 400
    assert "offline" in r.json()["detail"]


def test_manual_assign_non_pending_ride_rejected():
    _driver("d@t.com", 51.0, -114.0)
    ride_id = _ride(status="assigned")

    r = client.post(f"/rides/{ride_id}/assign", json={"driver_email": "d@t.com"})
    assert r.status_code == 400


def test_manual_assign_unknown_driver_returns_404():
    ride_id = _ride()
    r = client.post(f"/rides/{ride_id}/assign", json={"driver_email": "ghost@t.com"})
    assert r.status_code == 404


# ── auto-assign: happy path ───────────────────────────────────────────────────

def test_auto_assign_picks_nearest():
    # far driver at lat 51.90, near driver at lat 51.05, pickup at 51.04
    _driver("far@t.com",  51.90, -114.0)
    _driver("near@t.com", 51.05, -114.0)
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "assigned"
    assert body["assigned_driver"]["email"] == "near@t.com"
    assert body["assigned_at"] is not None


def test_auto_assign_response_shape():
    """Response must match RideRequestOut shape, same as manual assign."""
    _driver("d@t.com", 51.05, -114.0)
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    body = client.post(f"/rides/{ride_id}/auto-assign").json()
    for field in ("id", "pickup_text", "dropoff_text", "status", "assigned_at", "created_at"):
        assert field in body


# ── auto-assign: tie-breaker ──────────────────────────────────────────────────

def test_auto_assign_tie_breaker_lower_id_wins():
    # Two drivers at identical distance — lower id must win.
    id1 = _driver("first@t.com",  51.05, -114.0)
    id2 = _driver("second@t.com", 51.05, -114.0)
    assert id1 < id2  # confirm seeding order
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 200
    assert r.json()["assigned_driver"]["email"] == "first@t.com"


# ── auto-assign: error paths ──────────────────────────────────────────────────

def test_auto_assign_no_coords_returns_400():
    _driver("d@t.com", 51.0, -114.0)
    ride_id = _ride()  # no pickup_lat/lon

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 400
    assert "coordinates" in r.json()["detail"]


def test_auto_assign_no_drivers_returns_409():
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 409
    assert "No available drivers" in r.json()["detail"]


def test_auto_assign_non_pending_returns_400():
    _driver("d@t.com", 51.0, -114.0)
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0, status="assigned")

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 400
    assert "assigned" in r.json()["detail"]


def test_auto_assign_missing_ride_returns_404():
    r = client.post("/rides/99999/auto-assign")
    assert r.status_code == 404


# ── auto-assign: candidate filtering ─────────────────────────────────────────

def test_auto_assign_skips_offline_driver():
    _driver("offline@t.com", 51.04, -114.0, status="offline")
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 409  # offline driver is not a candidate


def test_auto_assign_skips_inactive_driver():
    _driver("inactive@t.com", 51.04, -114.0, is_active=False)
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 409  # inactive driver is not a candidate


def test_auto_assign_skips_driver_without_location():
    # Driver exists and is available, but has no DriverLocation row.
    _driver_no_location("noloc@t.com")
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 409  # no DriverLocation → excluded from join


def test_auto_assign_only_selects_available_among_mixed():
    # One offline, one available — available must win even though offline is closer.
    _driver("offline_near@t.com", 51.041, -114.0, status="offline")
    _driver("available_far@t.com", 51.20,  -114.0, status="available")
    ride_id = _ride(pickup_lat=51.04, pickup_lon=-114.0)

    r = client.post(f"/rides/{ride_id}/auto-assign")
    assert r.status_code == 200
    assert r.json()["assigned_driver"]["email"] == "available_far@t.com"


# ── create-time assignment_mode ───────────────────────────────────────────────

def test_create_auto_mode_assigns_nearest_driver():
    _driver("near@t.com", 51.05, -114.0)
    _driver("far@t.com",  51.90, -114.0)

    r = client.post("/rides/", json={
        "pickup_text": "A", "dropoff_text": "B",
        "pickup_lat": 51.04, "pickup_lon": -114.0,
        "assignment_mode": "auto",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "assigned"
    assert body["assigned_driver"]["email"] == "near@t.com"
    assert body["assigned_at"] is not None


def test_create_auto_mode_missing_coords_returns_400():
    _driver("d@t.com", 51.0, -114.0)

    r = client.post("/rides/", json={
        "pickup_text": "A", "dropoff_text": "B",
        "assignment_mode": "auto",
    })
    assert r.status_code == 400
    assert "coordinates" in r.json()["detail"]


def test_create_auto_mode_no_drivers_returns_409():
    r = client.post("/rides/", json={
        "pickup_text": "A", "dropoff_text": "B",
        "pickup_lat": 51.04, "pickup_lon": -114.0,
        "assignment_mode": "auto",
    })
    assert r.status_code == 409
    assert "No available drivers" in r.json()["detail"]


def test_create_omitting_assignment_mode_stays_pending():
    r = client.post("/rides/", json={"pickup_text": "A", "dropoff_text": "B"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["assigned_driver"] is None


# ── cancel ────────────────────────────────────────────────────────────────────

def test_cancel_pending_ride_succeeds():
    ride_id = _ride()
    r = client.post(f"/rides/{ride_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_cancel_non_pending_ride_returns_400():
    ride_id = _ride(status="assigned")
    r = client.post(f"/rides/{ride_id}/cancel")
    assert r.status_code == 400
    assert "assigned" in r.json()["detail"]


def test_cancel_missing_ride_returns_404():
    r = client.post("/rides/99999/cancel")
    assert r.status_code == 404
