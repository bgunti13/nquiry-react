from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    user_id: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    organization_data: Optional[dict] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    show_ticket_form: bool = False
    suggested_actions: Optional[List[str]] = None

class ChatHistory(BaseModel):
    """Chat history model"""
    id: Optional[str] = None
    user_id: str
    role: str  # 'user' or 'assistant'
    message: str
    timestamp: datetime

class InitializeRequest(BaseModel):
    """Request to initialize the query processor"""
    organization_data: dict