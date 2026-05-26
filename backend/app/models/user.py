from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole"), nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="userstatus"),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default="'ACTIVE'",
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", use_alter=True, name="fk_users_updated_by_user_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    driver_profile: Mapped["DriverProfile | None"] = relationship(
        "DriverProfile", back_populates="user", uselist=False
    )
    customer_profile: Mapped["CustomerProfile | None"] = relationship(
        "CustomerProfile", back_populates="user", uselist=False
    )
