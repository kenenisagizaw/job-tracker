from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.repositories import user_repository


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])

    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise credentials_exception

    user = user_repository.get_by_id(db, user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user