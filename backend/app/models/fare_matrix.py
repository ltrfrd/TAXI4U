from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class FareMatrix(Base):
    __tablename__ = "fare_matrix"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pickup_zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("zones.id"), nullable=False
    )
    dropoff_zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("zones.id"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    pickup_zone: Mapped["Zone"] = relationship(
        "Zone", foreign_keys="[FareMatrix.pickup_zone_id]"
    )
    dropoff_zone: Mapped["Zone"] = relationship(
        "Zone", foreign_keys="[FareMatrix.dropoff_zone_id]"
    )
