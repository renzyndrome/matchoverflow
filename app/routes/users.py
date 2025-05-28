from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from ..models.database import get_db
from ..models import user as user_models
from ..models import schemas
from ..utils.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: user_models.User = Depends(get_current_active_user)):
    return current_user

@router.put("/me", response_model=schemas.User)
async def update_user(
    user_update: schemas.UserUpdate,
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    if user_update.age is not None:
        current_user.age = user_update.age
    if user_update.looking_for is not None:
        current_user.looking_for = user_update.looking_for
    if user_update.traits is not None:
        current_user.traits = json.dumps(user_update.traits)
    if user_update.match_preference is not None:
        current_user.match_preference = user_update.match_preference
    if user_update.profile_picture is not None:
        current_user.profile_picture = user_update.profile_picture
    
    # Update interests
    if user_update.interests is not None:
        # Clear existing interests
        current_user.interests = []
        
        # Add new interests
        for interest_name in user_update.interests:
            interest = db.query(user_models.Interest).filter(
                user_models.Interest.name == interest_name
            ).first()
            
            if not interest:
                interest = user_models.Interest(name=interest_name)
                db.add(interest)
                db.commit()
            
            current_user.interests.append(interest)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/profile/{user_id}", response_model=schemas.UserProfile)
async def get_user_profile(
    user_id: int,
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    user = db.query(user_models.User).filter(user_models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert to UserProfile
    user_profile = schemas.UserProfile(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        age=user.age,
        looking_for=user.looking_for,
        profile_picture=user.profile_picture,
        is_active=user.is_active,
        created_at=user.created_at,
        interests=user.interests,
        traits=json.loads(user.traits) if user.traits else [],
        match_preference=user.match_preference
    )
    
    return user_profile

@router.get("/interests", response_model=List[schemas.Interest])
async def get_all_interests(db: Session = Depends(get_db)):
    interests = db.query(user_models.Interest).all()
    return interests 