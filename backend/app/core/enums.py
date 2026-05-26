from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DISPATCHER = "DISPATCHER"
    DRIVER = "DRIVER"
    CUSTOMER = "CUSTOMER"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class VehicleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class TripType(str, Enum):
    APP_REQUEST = "APP_REQUEST"
    PHONE_REQUEST = "PHONE_REQUEST"


class TripStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    ARRIVED = "ARRIVED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DECLINED = "DECLINED"
