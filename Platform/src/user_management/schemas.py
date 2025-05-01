from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class SocialLinks(BaseModel):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None

class Preferences(BaseModel):
    theme: Optional[str] = "light"
    editorSettings: Optional[Dict[str, Any]] = {}
    notifications: Optional[bool] = True

class Stats(BaseModel):
    problemsSolved: Optional[int] = 0
    totalSubmissions: Optional[int] = 0
    successfulSubmissions: Optional[int] = 0
    rank: Optional[int] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    role: Optional[list[str]] = None
    profilePicture: Optional[str] = None
    bio: Optional[str] = None
    socialLinks: Optional[SocialLinks] = None
    preferences: Optional[Preferences] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: str = Field(..., alias="_id")
    stats: Optional[Stats] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    lastLogin: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

class Token(BaseModel):
    access_token: str
    token_type: str