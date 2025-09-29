from sqlalchemy.orm import Session
import sys
import os
import uuid
import json
import time
from services.ai_service import AIService
from utils.context_memory_tmp import ConversationCache

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.conversation import Conversation, Message
from schemas.conversation import (
    ChatRequest
)
from models.user import User
# 导入文件工具函数
from utils.file_utils import extract_filename_from_url

ai_service = AIService()
cache = ConversationCache(max_size=1000, ttl=24*3600, max_context_length=10000)

def get_llm_models():
    return ai_service.get_available_models()

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
    # 如果有file_url，提取其中的文件名
    filename = None
    if file_url:
        filename = extract_filename_from_url(file_url)
    
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
    
    # 如果提取到文件名，可以在这里进行额外处理
    if filename:
        # 可以添加额外的文件处理逻辑
        pass
        
    return db_message

def get_messages(db: Session, conversation_id: int):
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()


def generate_agui_events(chat_request: ChatRequest, db: Session, current_user: User):
    """
    增加上下文记忆功能，框架采用mem0,每次请求时，获取当前会话的历史消息，作为上下文传递给模型。
    """
    cache.add_message(str(current_user.id), str(chat_request.conversation_id), "user", chat_request.message)
    context = cache.get_context(str(current_user.id), str(chat_request.conversation_id))
    context = f'当前提问：{context}|历史提问记录：{chat_request.message}'
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
    
    # Send text message start event
    message_id = str(uuid.uuid4())
    yield f"data: {json.dumps({'type': 'text_message_start', 'data': {'message_id': message_id, 'role': 'assistant'}})}\n\n"

    # Collect thinking process
    thinking_process = ""
    # Get AI response with streaming
    ai_response = ""
    for chunk in ai_service.chat_completion(
        chat_request.model, 
        context, 
        str(current_user.id),
        chat_request.file_url,
        chat_request.message_type
    ):
        if chunk.startswith("<think>") and chunk.endswith("</think>"):
            chunk = chunk[len("<think>"):-len("</think>")]
            thinking_process += chunk
            # Send thinking process delta event
            yield f"data: {json.dumps({'type': 'thinking_process', 'data': {'message': chunk}})}\n\n"
            continue
        if chunk.startswith("<content>") and chunk.endswith("</content>"):
            chunk = chunk[len("<content>"):-len("</content>")]
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

    # Send thinking process end event
    yield f"data: {json.dumps({'type': 'thinking_end', 'data': {'message': 'Thinking completed'}})}\n\n"
    
    # Send text message end event
    yield f"data: {json.dumps({'type': 'text_message_end', 'data': {'message_id': message_id}})}\n\n"
    
    # Send run end event
    yield f"data: {json.dumps({'type': 'run_end', 'data': {'run_id': run_id, 'message_id': ai_message.id}})}\n\n"
