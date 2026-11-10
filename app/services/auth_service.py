from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def register_user(db: Session, payload: UserCreate) -> User:
    email = str(payload.email).strip().lower()
    existing_user = user_repository.get_by_email(
        db,
        email,
    )

    if existing_user:
        raise EmailAlreadyRegisteredError("Email already registered")

    try:
        user = user_repository.create(
            db,
            email=email,
            hashed_password=hash_password(payload.password),
        )

        db.commit()
        db.refresh(user)

        return user

    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegisteredError("Email already registered")

    except Exception:
        db.rollback()
        raise


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> str:

    user = user_repository.get_by_email(db, email.strip().lower())

    if not user or not verify_password(
        password,
        user.hashed_password,
    ):
        raise InvalidCredentialsError("Incorrect email or password")

    if not user.is_active:
        raise InvalidCredentialsError("Inactive user")

    return create_access_token(user.id)