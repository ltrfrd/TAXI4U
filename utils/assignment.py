from sqlalchemy.orm import Session

from models.driver import Driver
from models.driver_location import DriverLocation


def _dist(a_lat, a_lon, b_lat, b_lon):
    return (a_lat - b_lat) ** 2 + (a_lon - b_lon) ** 2


def find_nearest_driver(
    pickup_lat: float,
    pickup_lon: float,
    db: Session,
    exclude_id: int | None = None,
) -> Driver | None:
    rows = (
        db.query(Driver, DriverLocation)
        .join(DriverLocation, DriverLocation.driver_id == Driver.id)
        .filter(Driver.is_active.is_(True), Driver.status == "available")
        .all()
    )
    if exclude_id is not None:
        rows = [r for r in rows if r[0].id != exclude_id]
    if not rows:
        return None
    rows.sort(
        key=lambda r: (
            _dist(pickup_lat, pickup_lon, r[1].latitude, r[1].longitude),
            r[0].id,
        )
    )
    return rows[0][0]
