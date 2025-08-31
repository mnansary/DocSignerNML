from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps

router = APIRouter()


@router.post("/", response_model=models.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: models.UserCreate,
):
    """
    Create new user.
    """
    user = crud.user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create_user(db, obj_in=user_in)
    return user
