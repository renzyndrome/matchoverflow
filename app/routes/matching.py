from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
import json

from ..models.database import get_db
from ..models import user as user_models
from ..models import schemas
from ..utils.auth import get_current_active_user
from ..services.matching import MatchingService

router = APIRouter(prefix="/matching", tags=["matching"])

@router.get("/find-matches", response_model=List[schemas.MatchResult])
async def find_matches(
    min_match_percentage: int = 75,
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Find potential matches for the current user with at least min_match_percentage compatibility"""
    matching_service = MatchingService()
    matches = matching_service.find_matches(current_user, db, min_match_percentage)
    return matches

@router.post("/pick", response_model=schemas.Pick)
async def pick_user(
    pick_data: schemas.PickCreate,
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Pick a user as a potential match"""
    # Check if user exists
    picked_user = db.query(user_models.User).filter(
        user_models.User.id == pick_data.picked_user_id
    ).first()
    
    if not picked_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already picked
    existing_pick = db.query(user_models.Pick).filter(
        user_models.Pick.picker_id == current_user.id,
        user_models.Pick.picked_id == pick_data.picked_user_id
    ).first()
    
    if existing_pick:
        raise HTTPException(status_code=400, detail="Already picked this user")
    
    # Calculate match percentage
    matching_service = MatchingService()
    match_percentage, _, _ = matching_service.calculate_match_percentage(current_user, picked_user)
    
    # Create pick
    db_pick = user_models.Pick(
        picker_id=current_user.id,
        picked_id=pick_data.picked_user_id,
        match_percentage=match_percentage
    )
    
    # Check if it's a mutual pick
    reverse_pick = db.query(user_models.Pick).filter(
        user_models.Pick.picker_id == pick_data.picked_user_id,
        user_models.Pick.picked_id == current_user.id
    ).first()
    
    if reverse_pick:
        # It's a match!
        db_pick.is_mutual = True
        reverse_pick.is_mutual = True
        
        # Add to matches
        current_user.matches.append(picked_user)
        
        # Create notifications for both users
        notification1 = user_models.Notification(
            user_id=current_user.id,
            message=f"It's a match! You and {picked_user.username} have matched!"
        )
        notification2 = user_models.Notification(
            user_id=picked_user.id,
            message=f"It's a match! You and {current_user.username} have matched!"
        )
        
        db.add(notification1)
        db.add(notification2)
    
    db.add(db_pick)
    db.commit()
    db.refresh(db_pick)
    
    return db_pick

@router.get("/picks/sent", response_model=List[schemas.Pick])
async def get_sent_picks(
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all picks sent by the current user"""
    return current_user.picks_made

@router.get("/picks/received", response_model=List[schemas.Pick])
async def get_received_picks(
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all picks received by the current user"""
    return current_user.picks_received

@router.get("/matches", response_model=List[schemas.UserProfile])
async def get_matches(
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all mutual matches for the current user"""
    # Get all mutual picks where current user is involved
    mutual_picks = db.query(user_models.Pick).filter(
        user_models.Pick.is_mutual == True,
        or_(
            user_models.Pick.picker_id == current_user.id,
            user_models.Pick.picked_id == current_user.id
        )
    ).all()
    
    matches = []
    matched_user_ids = set()
    
    for pick in mutual_picks:
        # Determine which user is the match
        if pick.picker_id == current_user.id:
            match_id = pick.picked_id
        else:
            match_id = pick.picker_id
            
        # Avoid duplicates
        if match_id in matched_user_ids:
            continue
            
        matched_user_ids.add(match_id)
        
        # Get the matched user
        matched_user = db.query(user_models.User).filter(
            user_models.User.id == match_id
        ).first()
        
        if matched_user:
            user_profile = schemas.UserProfile(
                id=matched_user.id,
                username=matched_user.username,
                full_name=matched_user.full_name,
                bio=matched_user.bio,
                age=matched_user.age,
                looking_for=matched_user.looking_for,
                profile_picture=matched_user.profile_picture,
                is_active=matched_user.is_active,
                created_at=matched_user.created_at,
                interests=matched_user.interests,
                match_preference=matched_user.match_preference,
                traits=json.loads(matched_user.traits) if matched_user.traits else [],
                match_percentage=pick.match_percentage
            )
            matches.append(user_profile)
    
    return matches

@router.get("/notifications", response_model=List[schemas.Notification])
async def get_notifications(
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current user"""
    return current_user.notifications

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(user_models.Notification).filter(
        user_models.Notification.id == notification_id,
        user_models.Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.get("/match-details/{user_id}", response_model=schemas.MatchResult)
async def get_match_details(
    user_id: int,
    current_user: user_models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed match information including compatibility reasons"""
    # Get the matched user
    matched_user = db.query(user_models.User).filter(
        user_models.User.id == user_id
    ).first()
    
    if not matched_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if they are actually matched
    is_matched = db.query(user_models.Pick).filter(
        user_models.Pick.is_mutual == True,
        or_(
            (user_models.Pick.picker_id == current_user.id) & (user_models.Pick.picked_id == user_id),
            (user_models.Pick.picker_id == user_id) & (user_models.Pick.picked_id == current_user.id)
        )
    ).first()
    
    if not is_matched:
        raise HTTPException(status_code=403, detail="You are not matched with this user")
    
    # Calculate match details using the matching service
    matching_service = MatchingService()
    match_percentage, common_interests, compatibility_reasons = matching_service.calculate_match_percentage(
        current_user, matched_user
    )
    
    # Create user profile
    user_profile = schemas.UserProfile(
        id=matched_user.id,
        username=matched_user.username,
        full_name=matched_user.full_name,
        bio=matched_user.bio,
        age=matched_user.age,
        looking_for=matched_user.looking_for,
        profile_picture=matched_user.profile_picture,
        is_active=matched_user.is_active,
        created_at=matched_user.created_at,
        interests=matched_user.interests,
        match_preference=matched_user.match_preference,
        traits=json.loads(matched_user.traits) if matched_user.traits else [],
        match_percentage=match_percentage
    )
    
    # Return match result with compatibility info
    return schemas.MatchResult(
        user=user_profile,
        match_percentage=match_percentage,
        common_interests=common_interests,
        compatibility_reasons=compatibility_reasons
    ) 