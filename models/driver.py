from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(String, nullable=False, default="offline", server_default="offline")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
