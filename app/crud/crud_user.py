import uuid
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.models.user import User
from app.models.user import UserCreate


def get(db: Session, id: uuid.UUID) -> User | None:
    """
    Gets a user by their ID.
    """
    return db.query(User).filter(User.id == id).first()


def get_user_by_email(db: Session, *, email: str) -> User | None:
    """
    Gets a user by their email address.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, *, obj_in: UserCreate) -> User:
    """
    Creates a new user.
    """
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        full_name=obj_in.full_name,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
