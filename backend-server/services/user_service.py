from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
import hashlib

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone == phone).first()

def create_user(db: Session, username: str, email: str, phone: str, password: str):
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    db_user = User(username=username, email=email, phone=phone, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, password: str, email: str = None, phone: str = None):
    if email:
        user = get_user_by_email(db, email)
    elif phone:
        user = get_user_by_phone(db, phone)
    else:
        return None
    
    if not user:
        return None
    
    # Check password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if user.password_hash != hashed_password:
        return None
    
    return user