from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base
import enum

# Association table for many-to-many relationship between users (matches)
user_matches = Table('user_matches', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('matched_user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

# Association table for user interests
user_interests = Table('user_interests', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('interest_id', Integer, ForeignKey('interests.id'))
)

class LookingForEnum(str, enum.Enum):
    buddy = "buddy"
    date = "date"
    both = "both"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    bio = Column(Text)
    age = Column(Integer)
    looking_for = Column(Enum(LookingForEnum), default=LookingForEnum.buddy)
    traits = Column(Text, default="[]")  # JSON string of traits
    match_preference = Column(Text)  # User's description of ideal match
    profile_picture = Column(String)  # URL or base64 of profile picture
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interests = relationship("Interest", secondary=user_interests, back_populates="users")
    matches = relationship(
        "User",
        secondary=user_matches,
        primaryjoin=id == user_matches.c.user_id,
        secondaryjoin=id == user_matches.c.matched_user_id,
        backref="matched_by"
    )
    picks_made = relationship("Pick", foreign_keys="Pick.picker_id", back_populates="picker")
    picks_received = relationship("Pick", foreign_keys="Pick.picked_id", back_populates="picked")
    notifications = relationship("Notification", back_populates="user")

class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)
    
    users = relationship("User", secondary=user_interests, back_populates="interests")

class Pick(Base):
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True, index=True)
    picker_id = Column(Integer, ForeignKey("users.id"))
    picked_id = Column(Integer, ForeignKey("users.id"))
    match_percentage = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_mutual = Column(Boolean, default=False)
    
    picker = relationship("User", foreign_keys=[picker_id], back_populates="picks_made")
    picked = relationship("User", foreign_keys=[picked_id], back_populates="picks_received")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications") 