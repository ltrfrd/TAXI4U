from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    assigned_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    driver: Mapped["User"] = relationship(
        "User", foreign_keys="[DriverVehicleAssignment.driver_user_id]"
    )
    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle", foreign_keys="[DriverVehicleAssignment.vehicle_id]"
    )
