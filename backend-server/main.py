import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from sqlalchemy.orm import Session
import os
import uuid

from config.database import get_db, engine
from models import Base
from models.user import User
from models.conversation import Conversation, Message
from services.user_service import create_user, authenticate_user
from services.conversation_service import (
    get_conversations, 
    create_conversation, 
    delete_conversation, 
    add_message, 
    get_messages
)
from services.ai_service import AIService

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize AI service
ai_service = AIService()

# Global variable to store user session
current_user = None

def login(email_or_phone: str, password: str):
    global current_user
    db: Session = next(get_db())
    
    # Try to authenticate with email or phone
    if "@" in email_or_phone:
        user = authenticate_user(db, password=password, email=email_or_phone)
    else:
        user = authenticate_user(db, password=password, phone=email_or_phone)
    
    if user:
        current_user = user
        return f"Welcome {user.username}!", get_conversations_list()
    else:
        return "Invalid credentials!", []

def logout():
    global current_user
    current_user = None
    return "Logged out successfully!", []

def register(username: str, email: str, phone: str, password: str):
    db: Session = next(get_db())
    
    try:
        user = create_user(db, username, email, phone, password)
        return f"User {user.username} registered successfully!"
    except Exception as e:
        return f"Registration failed: {str(e)}"

def get_conversations_list():
    if not current_user:
        return []
    
    db: Session = next(get_db())
    conversations = get_conversations(db, current_user.id)
    return [(conv.title, conv.id) for conv in conversations]

def create_new_conversation(title: str):
    if not current_user:
        return "Please log in first!", []
    
    db: Session = next(get_db())
    conversation = create_conversation(db, current_user.id, title)
    return f"Conversation '{title}' created!", get_conversations_list()

def delete_selected_conversation(conversation_id: int):
    if not current_user:
        return "Please log in first!", []
    
    db: Session = next(get_db())
    if delete_conversation(db, conversation_id):
        return "Conversation deleted!", get_conversations_list()
    else:
        return "Failed to delete conversation!", get_conversations_list()

def load_conversation(conversation_id: int):
    if not current_user:
        return "Please log in first!", []
    
    db: Session = next(get_db())
    messages = get_messages(db, conversation_id)
    chat_history = [(msg.content, msg.role) for msg in messages]
    return chat_history

def chat_with_ai(conversation_id: int, model: str, message: str, chat_history: list):
    if not current_user:
        yield "Please log in first!", chat_history
    
    db: Session = next(get_db())
    
    # Add user message to database
    user_message = add_message(db, conversation_id, message, "user")
    chat_history.append((message, "user"))
    yield "", chat_history
    
    # Get AI response
    ai_response = ""
    chat_history.append((ai_response, "assistant"))
    
    # Stream AI response
    for chunk in ai_service.chat_completion(model, message, str(current_user.id)):
        ai_response += chunk
        chat_history[-1] = (ai_response, "assistant")
        yield "", chat_history
    
    # Save AI response to database
    add_message(db, conversation_id, ai_response, "assistant")

def get_available_models():
    return ai_service.get_available_models()

with gr.Blocks(title="AI Chat Application") as app:
    gr.Markdown("# AI Chat Application")
    
    with gr.Tab("Login"):
        login_email_phone = gr.Textbox(label="Email or Phone")
        login_password = gr.Textbox(label="Password", type="password")
        login_button = gr.Button("Login")
        logout_button = gr.Button("Logout")
        login_output = gr.Textbox(label="Status")
        conversations_dropdown = gr.Dropdown(label="Your Conversations", choices=[], interactive=True)
        
    with gr.Tab("Register"):
        reg_username = gr.Textbox(label="Username")
        reg_email = gr.Textbox(label="Email")
        reg_phone = gr.Textbox(label="Phone")
        reg_password = gr.Textbox(label="Password", type="password")
        register_button = gr.Button("Register")
        register_output = gr.Textbox(label="Status")
        
    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column(scale=1):
                model_choice = gr.Dropdown(choices=get_available_models(), label="Select Model", value=get_available_models()[0] if get_available_models() else "")
                conversation_title = gr.Textbox(label="New Conversation Title")
                create_conv_button = gr.Button("Create New Conversation")
                delete_conv_button = gr.Button("Delete Selected Conversation")
                refresh_conv_button = gr.Button("Refresh Conversations")
                
            with gr.Column(scale=3):
                chatbot = gr.Chatbot()
                msg = gr.Textbox(label="Message")
                clear = gr.Button("Clear Chat")
                
    # Event handlers
    login_button.click(
        login, 
        inputs=[login_email_phone, login_password], 
        outputs=[login_output, conversations_dropdown]
    )
    
    logout_button.click(
        logout,
        outputs=[login_output, conversations_dropdown]
    )
    
    register_button.click(
        register,
        inputs=[reg_username, reg_email, reg_phone, reg_password],
        outputs=register_output
    )
    
    create_conv_button.click(
        create_new_conversation,
        inputs=conversation_title,
        outputs=[login_output, conversations_dropdown]
    )
    
    delete_conv_button.click(
        delete_selected_conversation,
        inputs=conversations_dropdown,
        outputs=[login_output, conversations_dropdown]
    )
    
    refresh_conv_button.click(
        get_conversations_list,
        outputs=conversations_dropdown
    )
    
    conversations_dropdown.change(
        load_conversation,
        inputs=conversations_dropdown,
        outputs=chatbot
    )
    
    msg.submit(
        chat_with_ai,
        inputs=[conversations_dropdown, model_choice, msg, chatbot],
        outputs=[msg, chatbot]
    )
    
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    app.launch()