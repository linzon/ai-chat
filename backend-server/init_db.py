"""
Script to initialize the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine
from models import Base
from models.user import User
from models.conversation import Conversation, Message

def init_db():
    # Create all tables in the right order to handle foreign key constraints
    # The order matters because of foreign key relationships
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()