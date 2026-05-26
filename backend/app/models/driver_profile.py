from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    profile_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_online: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    total_trips: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    user: Mapped["User"] = relationship("User", back_populates="driver_profile")
