from datetime import datetime, timedelta, timezone
import os

from jose import jwt

from config import TAXI4U_DEV

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if not TAXI4U_DEV:
        raise RuntimeError("JWT_SECRET_KEY must be set when TAXI4U_DEV is disabled")
    SECRET_KEY = "taxi4u-dev-secret-change-in-production"
ALGORITHM = "HS256"
_EXPIRE_HOURS = 24


def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) + timedelta(hours=_EXPIRE_HOURS)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
