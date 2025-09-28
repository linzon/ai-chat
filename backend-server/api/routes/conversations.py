from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import sys
import os
import uuid
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from schemas.conversation import (
    Conversation, 
    ConversationCreate, 
    Message, 
    ChatRequest, 
    ChatResponse
)
from services.conversation_service import (
    generate_agui_events,
    get_conversations,
    get_conversation,
    create_conversation,
    update_conversation_title,
    delete_conversation,
    add_message,
    get_messages,
    get_llm_models
)
from api.deps import get_db_session, get_current_user
from models.user import User

router = APIRouter(prefix="/conversations", tags=["conversations"])

# 将 /models 路径放在最前面，避免被 /{conversation_id} 捕获
@router.get("/models")
def get_models():
    return {"models": get_llm_models()}

@router.get("/", response_model=List[Conversation])
def read_conversations(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return get_conversations(db, current_user.id)

@router.post("/", response_model=Conversation)
def create_new_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return create_conversation(db, current_user.id, conversation.title)

@router.put("/{conversation_id}", response_model=Conversation)
def update_conversation(
    conversation_id: int,
    conversation: ConversationCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Check if conversation belongs to user
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation or db_conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    updated_conversation = update_conversation_title(db, conversation_id, conversation.title)
    if not updated_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return updated_conversation

@router.get("/{conversation_id}", response_model=List[Message])
def read_messages(
    conversation_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Check if conversation belongs to user
    conversation = get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = get_messages(db, conversation_id)
    return messages

@router.delete("/{conversation_id}")
def remove_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Check if conversation belongs to user
    conversation = get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    result = delete_conversation(db, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted successfully"}

@router.post("/chat")
async def chat_with_ai(
    chat_request: ChatRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with AI using AG-UI protocol and SSE streaming
    """
    return StreamingResponse(
        generate_agui_events(chat_request, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )