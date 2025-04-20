from odmantic import Model, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import ConfigDict

class User(Model):
    username: str
    email: str
    password_hash: str
    salt: str
    firstName: str
    lastName: str
    role: List[str]
    profilePicture: Optional[str] = None
    bio: Optional[str] = None
    socialLinks: Optional[Dict[str, Any]] = {}
    preferences: Optional[Dict[str, Any]] = {}
    stats: Optional[Dict[str, Any]] = Field(default_factory=lambda: {
        "problemsSolved": 0,
        "totalSubmissions": 0,
        "successfulSubmissions": 0,
        "rank": None
    })
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    lastLogin: Optional[datetime] = None

    model_config = ConfigDict(collection="users")