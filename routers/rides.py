from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.driver import Driver
from models.ride_request import RideRequest
from schemas.driver import DriverPublic
from schemas.ride_request import AssignRideRequest, RideRequestCreate, RideRequestOut
from utils.assignment import find_nearest_driver

router = APIRouter(prefix="/rides", tags=["rides"])


def _do_assign(ride: RideRequest, driver: Driver, db: Session) -> None:
    ride.driver_id = driver.id
    ride.status = "assigned"
    ride.assigned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ride)


def _ride_out(ride: RideRequest, db: Session) -> dict:
    out = RideRequestOut.model_validate(ride).model_dump()
    if ride.driver_id:
        driver = db.get(Driver, ride.driver_id)
        if driver:
            out["assigned_driver"] = DriverPublic.model_validate(driver).model_dump()
    return out


@router.post("/", response_model=RideRequestOut, status_code=201)
def create_ride(payload: RideRequestCreate, db: Session = Depends(get_db)):
    ride = RideRequest(**payload.model_dump())
    db.add(ride)
    db.commit()
    db.refresh(ride)
    return _ride_out(ride, db)


@router.get("/", response_model=list[RideRequestOut])
def list_rides(db: Session = Depends(get_db)):
    rides = db.query(RideRequest).order_by(RideRequest.created_at.desc()).all()
    return [_ride_out(r, db) for r in rides]


@router.get("/{ride_id}", response_model=RideRequestOut)
def get_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.get(RideRequest, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride request not found")
    return _ride_out(ride, db)


@router.post("/{ride_id}/assign", response_model=RideRequestOut)
def assign_ride(ride_id: int, payload: AssignRideRequest, db: Session = Depends(get_db)):
    ride = db.get(RideRequest, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride request not found")
    if ride.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot assign a ride with status '{ride.status}'")

    driver = db.query(Driver).filter(Driver.email == payload.driver_email).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if not driver.is_active:
        raise HTTPException(status_code=400, detail="Driver account is inactive")
    if driver.status != "available":
        raise HTTPException(status_code=400, detail=f"Driver status is '{driver.status}', must be 'available'")

    _do_assign(ride, driver, db)
    return _ride_out(ride, db)


@router.post("/{ride_id}/auto-assign", response_model=RideRequestOut)
def auto_assign_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.get(RideRequest, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride request not found")
    if ride.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot assign a ride with status '{ride.status}'"
        )
    if ride.pickup_lat is None or ride.pickup_lon is None:
        raise HTTPException(
            status_code=400,
            detail="Ride has no pickup coordinates for auto-assignment"
        )

    driver = find_nearest_driver(ride.pickup_lat, ride.pickup_lon, db)
    if not driver:
        raise HTTPException(status_code=409, detail="No available drivers found")

    _do_assign(ride, driver, db)
    return _ride_out(ride, db)
