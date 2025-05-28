from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import json
import logging

from ..models.database import get_db
from ..models import user as user_models
from ..models import schemas
from ..utils.auth import (
    authenticate_user, create_access_token, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for username: {user.username}")
    
    # Check if username already exists
    db_user = db.query(user_models.User).filter(user_models.User.username == user.username).first()
    if db_user:
        logger.warning(f"Username already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = user_models.User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        bio=user.bio,
        age=user.age,
        looking_for=user.looking_for,
        traits=json.dumps(user.traits) if user.traits else "[]",
        match_preference=user.match_preference,
        profile_picture=user.profile_picture
    )
    
    db.add(db_user)
    db.commit()
    
    # Add interests
    if user.interests:
        for interest_name in user.interests:
            # Check if interest exists
            interest = db.query(user_models.Interest).filter(
                user_models.Interest.name == interest_name
            ).first()
            
            if not interest:
                # Create new interest
                interest = user_models.Interest(name=interest_name)
                db.add(interest)
                db.commit()
            
            db_user.interests.append(interest)
        
        db.commit()
    
    db.refresh(db_user)
    logger.info(f"User {user.username} registered successfully with profile picture: {'Yes' if user.profile_picture else 'No'}")
    return db_user

@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"} 