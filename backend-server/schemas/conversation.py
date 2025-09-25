from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    role: str
    message_type: str = "text"
    file_url: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    file_url: str
    conversation_id: int
    model: str
    message: str
    message_type: str = "text"

class ChatResponse(BaseModel):
    user_message: Message
    ai_message: Message