from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    driver: Mapped["User"] = relationship("User", foreign_keys="[DriverLocation.driver_user_id]")
