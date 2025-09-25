from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from . import Base

__all__ = ['Conversation', 'Message']

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    content = Column(Text)
    role = Column(String)  # 'user' or 'assistant'
    message_type = Column(String)  # 'text', 'image', 'document', 'audio'
    file_url = Column(String, nullable=True)  # 存储文件URL
    created_at = Column(DateTime, default=datetime.utcnow)