from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from config import TAXI4U_DEV
from database import get_db
from models.driver import Driver
from models.driver_location import DriverLocation
from models.ride_request import RideRequest
from schemas.ride_request import RideRequestOut
from schemas.driver import DriverCreate, DriverLogin, DriverOut, DriverStatus
from schemas.driver_location import LocationOut, LocationUpdate
from utils.assignment import find_nearest_driver
from utils.auth import hash_password, verify_password
from utils.jwt import create_access_token, verify_token
from utils.ride_helpers import _do_assign, _ride_out

router = APIRouter(prefix="/driver", tags=["driver"])

_bearer_scheme = HTTPBearer()


def get_current_driver(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Driver:
    try:
        payload = verify_token(credentials.credentials)
        driver_id: int = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    driver = db.get(Driver, driver_id)
    if not driver or not driver.is_active:
        raise HTTPException(status_code=401, detail="Driver not found or inactive")

    return driver


@router.post("/login")
def driver_login(payload: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.email == payload.email).first()

    if not driver or not verify_password(payload.password, driver.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not driver.is_active:
        raise HTTPException(status_code=403, detail="Driver account is inactive")

    token = create_access_token({"sub": str(driver.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/available")
def list_available_drivers(db: Session = Depends(get_db)):
    drivers = (
        db.query(Driver)
        .filter(Driver.status == "available", Driver.is_active.is_(True))
        .all()
    )
    return [DriverPublic.model_validate(d).model_dump() for d in drivers]


@router.get("/me")
def driver_me(current_driver: Driver = Depends(get_current_driver)):
    return DriverOut.model_validate(current_driver).model_dump()


@router.post("/status")
def update_status(
    payload: DriverStatus,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    current_driver.status = payload.status
    db.commit()
    return {"status": current_driver.status}


@router.post("/location")
def update_location(
    payload: LocationUpdate,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    loc = db.query(DriverLocation).filter(DriverLocation.driver_id == current_driver.id).first()
    if loc:
        loc.latitude = payload.latitude
        loc.longitude = payload.longitude
        loc.updated_at = datetime.now(timezone.utc)
    else:
        loc = DriverLocation(
            driver_id=current_driver.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        db.add(loc)
    db.commit()
    db.refresh(loc)
    return LocationOut.model_validate(loc).model_dump()


@router.get("/rides", response_model=list[RideRequestOut])
def driver_rides(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    rides = (
        db.query(RideRequest)
        .filter(RideRequest.driver_id == current_driver.id)
        .order_by(RideRequest.created_at.desc())
        .all()
    )
    return [_ride_out(r, db) for r in rides]


def _get_owned_ride(ride_id: int, driver: Driver, db: Session) -> RideRequest:
    ride = db.get(RideRequest, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.driver_id != driver.id:
        raise HTTPException(status_code=403, detail="This ride is not assigned to you")
    return ride


@router.post("/rides/{ride_id}/accept", response_model=RideRequestOut)
def accept_ride(
    ride_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    ride = _get_owned_ride(ride_id, current_driver, db)
    if ride.status != "assigned":
        raise HTTPException(status_code=400, detail=f"Cannot accept a ride with status '{ride.status}'")
    ride.status = "accepted"
    db.commit()
    db.refresh(ride)
    return _ride_out(ride, db)


@router.post("/rides/{ride_id}/decline", response_model=RideRequestOut)
def decline_ride(
    ride_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    ride = _get_owned_ride(ride_id, current_driver, db)
    if ride.status != "assigned":
        raise HTTPException(status_code=400, detail=f"Cannot decline a ride with status '{ride.status}'")
    ride.status = "pending"
    ride.driver_id = None
    ride.assigned_at = None
    db.commit()
    db.refresh(ride)

    if ride.pickup_lat is not None and ride.pickup_lon is not None:
        next_driver = find_nearest_driver(
            ride.pickup_lat, ride.pickup_lon, db, exclude_id=current_driver.id
        )
        if next_driver:
            _do_assign(ride, next_driver, db)

    return _ride_out(ride, db)


@router.post("/rides/{ride_id}/start", response_model=RideRequestOut)
def start_ride(
    ride_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    ride = _get_owned_ride(ride_id, current_driver, db)
    if ride.status != "accepted":
        raise HTTPException(status_code=400, detail=f"Cannot start a ride with status '{ride.status}'")
    ride.status = "in_progress"
    db.commit()
    db.refresh(ride)
    return _ride_out(ride, db)


@router.post("/rides/{ride_id}/complete", response_model=RideRequestOut)
def complete_ride(
    ride_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    ride = _get_owned_ride(ride_id, current_driver, db)
    if ride.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Cannot complete a ride with status '{ride.status}'")
    ride.status = "completed"
    db.commit()
    db.refresh(ride)
    return _ride_out(ride, db)


@router.get("/location/me")
def get_my_location(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    loc = db.query(DriverLocation).filter(DriverLocation.driver_id == current_driver.id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="No location recorded yet")
    return LocationOut.model_validate(loc).model_dump()


# DEV ONLY — remove or gate behind env flag before production
@router.post("/dev/create", tags=["dev"])
def dev_create_driver(payload: DriverCreate, db: Session = Depends(get_db)):
    if not TAXI4U_DEV:
        raise HTTPException(status_code=404, detail="Not found")

    if db.query(Driver).filter(Driver.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    driver = Driver(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    return {
        "message": "Driver created (dev only)",
        "driver": DriverOut.model_validate(driver).model_dump(),
    }
