from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from database import Base


class RideRequest(Base):
    __tablename__ = "ride_requests"

    id = Column(Integer, primary_key=True, index=True)
    pickup_text = Column(String, nullable=False)
    dropoff_text = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=True)
    pickup_lon = Column(Float, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lon = Column(Float, nullable=True)
    fare_amount = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending", server_default="pending")
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
