from datetime import datetime

from pydantic import BaseModel


class DriverCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str | None = None


class DriverLogin(BaseModel):
    email: str
    password: str


class DriverOut(BaseModel):
    name: str
    email: str
    phone: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
