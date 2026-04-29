from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.driver import Driver
from models.ride_request import RideRequest
from schemas.driver import DriverPublic
from schemas.ride_request import RideRequestOut


def _do_assign(ride: RideRequest, driver: Driver, db: Session) -> None:
    ride.driver_id = driver.id
    ride.status = "assigned"
    ride.assigned_at = datetime.now(timezone.utc)
    driver.status = "busy"
    db.commit()
    db.refresh(ride)


def _ride_out(ride: RideRequest, db: Session) -> dict:
    out = RideRequestOut.model_validate(ride).model_dump()
    if ride.driver_id:
        driver = db.get(Driver, ride.driver_id)
        if driver:
            out["assigned_driver"] = DriverPublic.model_validate(driver).model_dump()
    return out
