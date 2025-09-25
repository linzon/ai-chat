from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.conversation import Conversation, Message

def get_conversations(db: Session, user_id: int):
    return db.query(Conversation).filter(Conversation.user_id == user_id).all()

def get_conversation(db: Session, conversation_id: int):
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def create_conversation(db: Session, user_id: int, title: str):
    db_conversation = Conversation(user_id=user_id, title=title)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def update_conversation_title(db: Session, conversation_id: int, title: str):
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if db_conversation:
        db_conversation.title = title
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    return None

def delete_conversation(db: Session, conversation_id: int):
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if db_conversation:
        db.delete(db_conversation)
        db.commit()
        return True
    return False

def add_message(db: Session, conversation_id: int, content: str, role: str, message_type: str = "text", file_url: str = None):
    db_message = Message(
        conversation_id=conversation_id, 
        content=content, 
        role=role, 
        message_type=message_type,
        file_url=file_url
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages(db: Session, conversation_id: int):
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()