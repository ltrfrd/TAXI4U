from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from models.driver import Driver
from models.driver_location import DriverLocation
from schemas.driver import DriverCreate, DriverLogin, DriverOut
from schemas.driver_location import LocationOut, LocationUpdate
from utils.auth import hash_password, verify_password
from utils.jwt import create_access_token, verify_token

router = APIRouter(prefix="/driver", tags=["driver"])

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/driver/login")


def get_current_driver(token: str = Depends(_oauth2_scheme), db: Session = Depends(get_db)) -> Driver:
    try:
        payload = verify_token(token)
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


@router.get("/me")
def driver_me(current_driver: Driver = Depends(get_current_driver)):
    return DriverOut.model_validate(current_driver).model_dump()


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
