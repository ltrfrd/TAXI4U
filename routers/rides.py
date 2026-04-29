from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models.driver import Driver
from models.ride_request import RideRequest
from schemas.ride_request import AssignRideRequest, ManualRideRequestCreate, RideRequestCreate, RideRequestOut
from utils.assignment import find_nearest_driver
from utils.deps import get_current_driver
from utils.jwt import verify_token
from utils.ride_helpers import _do_assign, _ride_out

router = APIRouter(prefix="/rides", tags=["rides"])


def _optional_driver_id(request: Request) -> int | None:
    """Extract driver id from Bearer token if present; return None otherwise."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        return int(verify_token(auth[7:])["sub"])
    except Exception:
        return None
@router.post("/", response_model=RideRequestOut, status_code=201)
def create_ride(payload: RideRequestCreate, request: Request, db: Session = Depends(get_db)):
    driver = None
    if payload.assignment_mode == "auto":
        if payload.pickup_lat is None or payload.pickup_lon is None:
            raise HTTPException(status_code=400, detail="Ride has no pickup coordinates for auto-assignment")
        driver = find_nearest_driver(payload.pickup_lat, payload.pickup_lon, db)
        if not driver:
            raise HTTPException(status_code=409, detail="No available drivers found")

    ride_data = payload.model_dump(exclude={"assignment_mode"})
    creator_id = _optional_driver_id(request)
    if creator_id:
        ride_data["created_by_id"] = creator_id
    ride = RideRequest(**ride_data)
    db.add(ride)
    db.commit()
    db.refresh(ride)

    if payload.assignment_mode == "auto":
        _do_assign(ride, driver, db)

    return _ride_out(ride, db)


@router.post("/manual", response_model=RideRequestOut, status_code=201)
def create_manual_ride(payload: ManualRideRequestCreate, request: Request, db: Session = Depends(get_db)):
    ride_out = create_ride(
        RideRequestCreate(
            pickup_text=payload.pickup_text,
            dropoff_text=payload.dropoff_text,
            pickup_lat=payload.pickup_lat,
            pickup_lon=payload.pickup_lon,
            dropoff_lat=payload.dropoff_lat,
            dropoff_lon=payload.dropoff_lon,
            fare_amount=payload.fare_amount,
            assignment_mode="manual",
        ),
        request,
        db,
    )

    if not payload.driver_email:
        return ride_out

    ride = db.get(RideRequest, ride_out["id"])
    driver = db.query(Driver).filter(Driver.email == payload.driver_email).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if not driver.is_active:
        raise HTTPException(status_code=400, detail="Driver account is inactive")
    if driver.status != "available":
        raise HTTPException(status_code=400, detail=f"Driver status is '{driver.status}', must be 'available'")

    _do_assign(ride, driver, db)
    return _ride_out(ride, db)


@router.get("/", response_model=list[RideRequestOut])
def list_rides(db: Session = Depends(get_db)):
    rides = db.query(RideRequest).order_by(RideRequest.created_at.desc()).all()
    return [_ride_out(r, db) for r in rides]


@router.get("/me/latest", response_model=RideRequestOut)
def my_latest_ride(current_driver: Driver = Depends(get_current_driver), db: Session = Depends(get_db)):
    ride = (
        db.query(RideRequest)
        .filter(RideRequest.created_by_id == current_driver.id)
        .order_by(RideRequest.created_at.desc())
        .first()
    )
    if not ride:
        raise HTTPException(status_code=404, detail="No rides found")
    return _ride_out(ride, db)


@router.get("/{ride_id}", response_model=RideRequestOut)
def get_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.get(RideRequest, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride request not found")
    return _ride_out(ride, db)


@router.post("/{ride_id}/assign", response_model=RideRequestOut)
def assign_ride(
    ride_id: int,
    payload: AssignRideRequest,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
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
def auto_assign_ride(
    ride_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
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


@router.post("/{ride_id}/cancel", response_model=RideRequestOut)
def cancel_ride(
    ride_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    ride = db.get(RideRequest, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride request not found")
    if ride.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot cancel a ride with status '{ride.status}'")
    ride.status = "cancelled"
    db.commit()
    db.refresh(ride)
    return _ride_out(ride, db)
