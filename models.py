from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserProfile(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    profession: Optional[str] = None
    medical_history: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
