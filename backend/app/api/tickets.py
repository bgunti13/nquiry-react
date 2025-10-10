from fastapi import APIRouter, HTTPException
import random
from datetime import datetime
from app.models.ticket import TicketCreate, TicketResponse

router = APIRouter()

# In-memory storage for demo purposes
tickets_storage = {}

@router.post("/create", response_model=TicketResponse)
async def create_ticket(ticket_data: TicketCreate):
    """Create a new support ticket"""
    try:
        # Generate a ticket ID
        org_prefix = "TICK"
        if ticket_data.organization_data:
            org_name = ticket_data.organization_data.get('name', '').upper()
            if org_name:
                org_prefix = org_name[:4]
        
        ticket_id = f"{org_prefix}-{random.randint(10000, 99999)}"
        
        # Create ticket response
        ticket_response = TicketResponse(
            ticket_id=ticket_id,
            title=ticket_data.title,
            status="Open" if not ticket_data.isEscalation else "Escalated",
            priority=ticket_data.priority,
            category=ticket_data.category,
            created_at=datetime.utcnow(),
            escalated=ticket_data.isEscalation
        )
        
        # Store ticket (in production, save to database)
        tickets_storage[ticket_id] = {
            "ticket_data": ticket_data.dict(),
            "response": ticket_response.dict()
        }
        
        return ticket_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID"""
    try:
        if ticket_id not in tickets_storage:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket_info = tickets_storage[ticket_id]
        return TicketResponse(**ticket_info["response"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ticket: {str(e)}")

@router.get("/")
async def list_tickets(user_id: str = None, limit: int = 10):
    """List tickets, optionally filtered by user"""
    try:
        tickets = list(tickets_storage.values())
        
        if user_id:
            tickets = [t for t in tickets if t["ticket_data"]["user_id"] == user_id]
        
        # Limit results
        tickets = tickets[:limit]
        
        return {
            "tickets": [t["response"] for t in tickets],
            "total": len(tickets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tickets: {str(e)}")