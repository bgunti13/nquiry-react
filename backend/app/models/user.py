from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    """User/Organization model"""
    name: str
    email: str
    role: str = "Customer"
    organization: Optional[str] = None

class UserResponse(BaseModel):
    """User response model"""
    users: list[User]