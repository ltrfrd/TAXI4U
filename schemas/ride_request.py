from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RideStatus = Literal["pending", "assigned", "accepted", "in_progress", "completed", "cancelled"]


class RideRequestCreate(BaseModel):
    pickup_text: str
    dropoff_text: str
    pickup_lat: float | None = None
    pickup_lon: float | None = None
    dropoff_lat: float | None = None
    dropoff_lon: float | None = None
    fare_amount: float | None = None
    assignment_mode: Literal["manual", "auto"] = "manual"


class AssignRideRequest(BaseModel):
    driver_email: str


class RideRequestOut(BaseModel):
    id: int
    pickup_text: str
    dropoff_text: str
    pickup_lat: float | None
    pickup_lon: float | None
    dropoff_lat: float | None
    dropoff_lon: float | None
    fare_amount: float | None
    status: str
    assigned_at: datetime | None
    assigned_driver: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
