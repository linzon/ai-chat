# Backend Server for AI Chat Application

This directory contains the backend server implementation for the AI Chat application using:
- Python
- Gradio for the web interface
- FastAPI for RESTful API
- LangGraph for workflow management
- SQLite for database storage
- Mem0 for memory caching

## Features Implemented

1. User authentication (login/logout)
2. User registration with email or phone
3. Conversation history management (query, delete)
4. New conversation creation
5. AI chat functionality with streaming output
6. Support for multiple AI models (Qwen-2.5, Baichuan v1.0)

## Project Structure

```
backend-server/
├── api/             # FastAPI application and routes
│   ├── routes/      # API route definitions
│   ├── deps.py      # API dependencies
│   └── main.py      # FastAPI application entry point
├── config/          # Configuration files
├── db/              # SQLite database files
├── models/          # Database models
├── schemas/         # Pydantic models for request/response validation
├── services/        # Business logic services
├── utils/           # Utility functions
├── main.py          # Gradio application
├── init_db.py       # Database initialization script
└── requirements.txt # Python dependencies
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```
   python init_db.py
   ```

3. Run the applications:

   For FastAPI RESTful API:
   ```
   uvicorn api.main:app --reload
   ```
   
   For Gradio interface:
   ```
   python main.py
   ```

The FastAPI application will be available at `http://localhost:8000` by default.
The Gradio application will be available at `http://localhost:7860` by default.

## API Endpoints

### Authentication
- `POST /users/register` - Register a new user
- `POST /users/login` - Login and get access token

### Conversations
- `GET /conversations/` - Get all conversations for the current user
- `POST /conversations/` - Create a new conversation
- `GET /conversations/{conversation_id}` - Get messages in a conversation
- `DELETE /conversations/{conversation_id}` - Delete a conversation
- `POST /conversations/chat` - Chat with AI
- `GET /conversations/models` - Get available AI models

### Health Check
- `GET /health` - Check if the API is running

## Features

### Authentication
- Login with email or phone
- User registration
- JWT token-based authentication

### Conversation Management
- Create new conversations
- View conversation history
- Delete conversations

### AI Chat
- Stream responses from AI models
- Support for multiple input types (text, image, document, voice)
- Switch between different AI models