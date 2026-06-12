from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from app.database import get_db
from app.models.conversations.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationRead)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    conversation = Conversation(id=uuid4(), **payload.dict())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
