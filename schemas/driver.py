from datetime import datetime
from typing import Literal

from pydantic import BaseModel

VALID_STATUSES = Literal["offline", "available", "busy"]


class DriverCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str | None = None


class DriverLogin(BaseModel):
    email: str
    password: str


class DriverStatus(BaseModel):
    status: VALID_STATUSES


class DriverOut(BaseModel):
    name: str
    email: str
    phone: str | None
    is_active: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DriverPublic(BaseModel):
    """Safe driver fields for public listing and ride assignment responses."""
    name: str
    email: str
    phone: str | None
    status: str

    model_config = {"from_attributes": True}
