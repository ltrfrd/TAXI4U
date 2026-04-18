from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.sql import func

from database import Base


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
