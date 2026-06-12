from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from app.database import get_db
from app.models.conversations.conversation import Message
from app.schemas.message import MessageCreate, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageRead)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    message = Message(id=uuid4(), **payload.dict())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/{message_id}", response_model=MessageRead)
def get_message(message_id: str, db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
