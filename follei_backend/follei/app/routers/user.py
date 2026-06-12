from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from app.database import get_db
from app.models.tenancy import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(id=uuid4(), **payload.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
