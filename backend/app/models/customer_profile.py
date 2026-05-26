from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    total_trips: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    user: Mapped["User"] = relationship("User", back_populates="customer_profile")
