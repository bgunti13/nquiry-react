from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    """Ticket creation model"""
    title: str
    description: str
    priority: str = "Medium"
    category: str = "General"
    isEscalation: bool = False
    user_id: str
    organization_data: Optional[dict] = None

class TicketResponse(BaseModel):
    """Ticket response model"""
    ticket_id: str
    title: str
    status: str
    priority: str
    category: str
    created_at: datetime
    escalated: bool = False