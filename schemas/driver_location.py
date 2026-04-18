from datetime import datetime

from pydantic import BaseModel


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


class LocationOut(BaseModel):
    latitude: float
    longitude: float
    updated_at: datetime

    model_config = {"from_attributes": True}
