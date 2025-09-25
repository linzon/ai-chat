from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import hashlib
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from schemas.user import User, UserCreate, UserLogin
from models.user import User as UserModel
from services.user_service import create_user, authenticate_user, get_user_by_id
from api.deps import get_db_session, create_access_token, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db_session)):
    # Check if user already exists
    existing_user = db.query(UserModel).filter(
        (UserModel.email == user.email) | (UserModel.phone == user.phone)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or phone already exists"
        )
    
    # Create new user
    db_user = create_user(
        db, 
        username=user.username,
        email=user.email, 
        phone=user.phone, 
        password=user.password
    )
    
    return db_user

@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db_session)):
    # Determine if email or phone is used
    if "@" in user.email_or_phone:
        db_user = authenticate_user(db, password=user.password, email=user.email_or_phone)
    else:
        db_user = authenticate_user(db, password=user.password, phone=user.email_or_phone)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {"access_token": access_token, "token_type": "bearer", "user": {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "phone": db_user.phone
    }}

@router.get("/me", response_model=User)
def read_users_me(current_user: UserModel = Depends(get_current_user)):
    return current_user