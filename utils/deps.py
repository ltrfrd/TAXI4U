from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from models.driver import Driver
from utils.jwt import verify_token

_bearer_scheme = HTTPBearer()


def get_current_driver(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Driver:
    try:
        payload = verify_token(credentials.credentials)
        driver_id: int = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    driver = db.get(Driver, driver_id)
    if not driver or not driver.is_active:
        raise HTTPException(status_code=401, detail="Driver not found or inactive")

    return driver
