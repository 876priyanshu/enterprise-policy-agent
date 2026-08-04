from sqlalchemy.orm import Session
from app.models.chat import Conversation, Message
import uuid
from fastapi import HTTPException
def get_or_create_conversation(db: Session, conversation_id: str | None, user_id: int):
    if conversation_id:
        # Check if conversation exists AND belongs to the user
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not conv:
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation.")
        return conv.id
        
    # If no ID is provided, create a new conversation tied to this user
    new_conv = Conversation(id=str(uuid.uuid4()), user_id=user_id)
    db.add(new_conv)
    db.commit()
    return new_conv.id

def add_message(db: Session, conversation_id: str, role: str, content: str):
    """Saves a single chat bubble to the database."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()

def get_conversation_history(db: Session, conversation_id: str):
    """Retrieves all messages for a conversation, ordered chronologically."""
    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.asc())\
        .all()
        
    return [{"role": msg.role, "content": msg.content} for msg in messages]