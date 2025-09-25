from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys

# Add the parent directory to the path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import users, conversations, uploads
from config.database import engine
from models import Base
from models.user import User
from models.conversation import Conversation, Message

# Create database tables
# 确保按照正确的顺序创建表以满足外键约束
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="AI Chat API",
    description="API for AI Chat Application with FastAPI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载上传文件目录为静态文件目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(uploads.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Chat API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)