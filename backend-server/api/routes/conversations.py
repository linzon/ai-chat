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
    get_conversations,
    get_conversation,
    create_conversation,
    update_conversation_title,
    delete_conversation,
    add_message,
    get_messages
)
from services.ai_service import AIService
from api.deps import get_db_session, get_current_user
from models.user import User

router = APIRouter(prefix="/conversations", tags=["conversations"])
ai_service = AIService()

# 将 /models 路径放在最前面，避免被 /{conversation_id} 捕获
@router.get("/models")
def get_models():
    return {"models": ["qwen-2.5", "baichuan-v1.0"]}

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

def generate_agui_events(chat_request: ChatRequest, db: Session, current_user: User):
    """
    Generate AG-UI protocol events for SSE streaming
    """
    # Check if conversation belongs to user
    conversation = get_conversation(db, chat_request.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        yield f"data: {json.dumps({'type': 'error', 'data': 'Conversation not found'})}\n\n"
        return
    
    # Add user message to database
    user_message = add_message(
        db, 
        chat_request.conversation_id, 
        chat_request.message, 
        "user",
        chat_request.message_type,
        chat_request.file_url
    )
    
    # Send user message event
    yield f"data: {json.dumps({'type': 'user_message', 'data': {'id': user_message.id, 'content': user_message.content, 'role': user_message.role, 'message_type': user_message.message_type}})}\n\n"
    
    # Send run start event
    run_id = str(uuid.uuid4())
    yield f"data: {json.dumps({'type': 'run_start', 'data': {'run_id': run_id}})}\n\n"
    
    # Send thinking process start event
    yield f"data: {json.dumps({'type': 'thinking_start', 'data': {'message': 'AI is thinking...'}})}\n\n"
    
    # Collect thinking process
    thinking_process = ""
    
    # Simulate thinking process events
    thinking_steps = [
        "Analyzing the user input...：First, the user said "". This seems like a random string of characters. I need to figure out what they mean or what they want. It might be a typo or a code. Since this is a conversation, I should respond in a helpful way.",
        "Retrieving relevant information..:First, the user said "". This seems like a random string of characters. I need to figure out what they mean or what they want. It might be a typo or a code. Since this is a conversation, I should respond in a helpful way..",
        "Processing the request...:First, the user said "". This seems like a random string of characters. I need to figure out what they mean or what they want. It might be a typo or a code. Since this is a conversation, I should respond in a helpful way.",
        "Generating response...L:First, the user said "". This seems like a random string of characters. I need to figure out what they mean or what they want. It might be a typo or a code. Since this is a conversation, I should respond in a helpful way."
    ]
    
    for step in thinking_steps:
        thinking_process += step + "\n"
        yield f"data: {json.dumps({'type': 'thinking_process', 'data': {'message': step}})}\n\n"
        time.sleep(0.3)  # Simulate processing time
    
    # Send thinking process end event
    yield f"data: {json.dumps({'type': 'thinking_end', 'data': {'message': 'Thinking completed'}})}\n\n"
    
    # Send text message start event
    message_id = str(uuid.uuid4())
    yield f"data: {json.dumps({'type': 'text_message_start', 'data': {'message_id': message_id, 'role': 'assistant'}})}\n\n"
    
    # Get AI response with streaming
    ai_response = ""
    for chunk in ai_service.chat_completion(
        chat_request.model, 
        chat_request.message, 
        str(current_user.id)
    ):
        ai_response += chunk
        # Send text message delta event
        yield f"data: {json.dumps({'type': 'text_message_delta', 'data': {'content': chunk}})}\n\n"
    
    # Save AI response to database with clear separation between thinking process and model response
    formatted_response = f"[思考过程]\n{thinking_process}\n[模型回复]\n{ai_response}"
    ai_message = add_message(
        db, 
        chat_request.conversation_id, 
        formatted_response, 
        "assistant",
        "text"
    )
    
    # Send text message end event
    yield f"data: {json.dumps({'type': 'text_message_end', 'data': {'message_id': message_id}})}\n\n"
    
    # Send run end event
    yield f"data: {json.dumps({'type': 'run_end', 'data': {'run_id': run_id, 'message_id': ai_message.id}})}\n\n"

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