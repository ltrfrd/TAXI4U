from datetime import datetime, timedelta, timezone

from jose import jwt

SECRET_KEY = "taxi4u-dev-secret-change-in-production"
ALGORITHM = "HS256"
_EXPIRE_HOURS = 24


def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) + timedelta(hours=_EXPIRE_HOURS)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
