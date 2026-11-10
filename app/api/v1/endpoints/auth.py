from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW_SECONDS
from app.core.redis import client as redis_client
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


def _check_login_rate_limit(
    client_key: str,
    client: object = redis_client,
) -> None:
    key = f"auth:login:rate:{client_key}"
    try:
        attempts = client.incr(key)
        if attempts == 1:
            client.expire(key, LOGIN_RATE_WINDOW_SECONDS)
    except RedisError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable",
        ) from error

    if attempts > LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
            headers={"Retry-After": str(LOGIN_RATE_WINDOW_SECONDS)},
        )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    try:
        return auth_service.register_user(db, payload)
    except auth_service.EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post("/token", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    client_host = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_host)
    try:
        token = auth_service.authenticate_user(
            db,
            email=form_data.username,
            password=form_data.password,
        )
        return {"access_token": token, "token_type": "bearer"}
    except auth_service.InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
