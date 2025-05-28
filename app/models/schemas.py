from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .user import LookingForEnum

class InterestBase(BaseModel):
    name: str
    category: Optional[str] = None

class InterestCreate(InterestBase):
    pass

class Interest(InterestBase):
    id: int
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    age: Optional[int] = None
    looking_for: LookingForEnum = LookingForEnum.buddy
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    password: str
    traits: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    match_preference: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    age: Optional[int] = None
    looking_for: Optional[LookingForEnum] = None
    traits: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    match_preference: Optional[str] = None
    profile_picture: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    interests: List[Interest] = []
    match_preference: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserProfile(User):
    match_percentage: Optional[int] = None
    traits: Optional[List[str]] = []

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PickCreate(BaseModel):
    picked_user_id: int

class Pick(BaseModel):
    id: int
    picker_id: int
    picked_id: int
    match_percentage: int
    created_at: datetime
    is_mutual: bool
    
    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    message: str

class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    user: UserProfile
    match_percentage: int
    common_interests: List[str]
    compatibility_reasons: List[str] 