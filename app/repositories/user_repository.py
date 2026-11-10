from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def create(db: Session, email: str, hashed_password: str) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
    )

    db.add(user)

    return user


def get_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)

    return db.scalar(statement)


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)