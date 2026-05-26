from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import TripStatus, TripType


class Trip(Base):
    __tablename__ = "trips"

    # Identity
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_type: Mapped[TripType] = mapped_column(
        SAEnum(TripType, name="triptype"), nullable=False
    )
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, name="tripstatus"),
        nullable=False,
        default=TripStatus.PENDING,
        server_default="'PENDING'",
    )

    # Parties
    customer_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    driver_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    dispatcher_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Location
    pickup_address: Mapped[str] = mapped_column(String(500), nullable=False)
    dropoff_address: Mapped[str] = mapped_column(String(500), nullable=False)
    pickup_zone_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("zones.id"), nullable=True
    )
    dropoff_zone_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("zones.id"), nullable=True
    )

    # Fare
    suggested_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    final_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fare_overridden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    stop_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    standby_minutes: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=0, server_default="0"
    )
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)

    # Assignment
    declined_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Timestamps
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    arrived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Audit
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Ratings
    driver_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    customer_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Relationships — operational parties only; audit FKs are plain columns
    customer: Mapped["User"] = relationship(
        "User", foreign_keys="[Trip.customer_user_id]"
    )
    driver: Mapped["User | None"] = relationship(
        "User", foreign_keys="[Trip.driver_user_id]"
    )
    dispatcher: Mapped["User | None"] = relationship(
        "User", foreign_keys="[Trip.dispatcher_user_id]"
    )
    pickup_zone: Mapped["Zone | None"] = relationship(
        "Zone", foreign_keys="[Trip.pickup_zone_id]"
    )
    dropoff_zone: Mapped["Zone | None"] = relationship(
        "Zone", foreign_keys="[Trip.dropoff_zone_id]"
    )
