from fastapi import APIRouter, HTTPException, Depends
from typing import List
import random
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to import from main directory
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(parent_dir)

from app.models.chat import ChatMessage, ChatResponse, ChatHistory, InitializeRequest

# Try to import the real intelligent processor
try:
    from main import nQuiryProcessor
    from config import Config
    INTELLIGENT_PROCESSOR_AVAILABLE = True
    print("✅ Intelligent nQuiry processor imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import intelligent processor: {e}")
    print("⚠️ Falling back to simple responses")
    INTELLIGENT_PROCESSOR_AVAILABLE = False

router = APIRouter()

# In-memory storage for demo purposes
# In production, this would use a proper database
chat_sessions = {}
chat_histories = {}

# Initialize intelligent processors
intelligent_processors = {}

async def get_intelligent_response(message: str, user_id: str, organization_data: dict = None) -> str:
    """Get response from the intelligent nQuiry processor"""
    try:
        if not INTELLIGENT_PROCESSOR_AVAILABLE:
            return get_fallback_response(message, organization_data)
        
        # Initialize processor for user if not exists
        if user_id not in intelligent_processors:
            config = Config()
            intelligent_processors[user_id] = nQuiryProcessor(config)
            print(f"🧠 Initialized intelligent processor for user: {user_id}")
        
        processor = intelligent_processors[user_id]
        
        # Create state for the processor
        state = {
            'query': message,
            'user_id': user_id,
            'organization_data': organization_data or {},
            'conversation_history': chat_histories.get(user_id, [])
        }
        
        # Process with the intelligent system
        print(f"🧠 Processing with intelligent nQuiry: '{message}'")
        result = await processor.process_query(state)
        
        if result and 'response' in result:
            return result['response']
        else:
            print("⚠️ Intelligent processor returned empty response")
            return get_fallback_response(message, organization_data)
            
    except Exception as e:
        print(f"❌ Error in intelligent processor: {e}")
        return get_fallback_response(message, organization_data)

def get_fallback_response(message: str, organization_data: dict = None) -> str:
    """Fallback response system"""
    print(f"🔤 Using fallback response for: '{message}'")
    
    message_lower = message.lower()
    org_name = organization_data.get('name', 'your organization') if organization_data else 'your organization'
    
    # CDM Workbench specific responses
    if 'cdm' in message_lower and 'workbench' in message_lower:
        if 'no data' in message_lower or 'report' in message_lower:
            return f"""**CDM Workbench "NO DATA TO REPORT" Solution for {org_name}**

🔍 **Common Root Causes:**
• Query filters too restrictive (date ranges, criteria)
• Data source issues (missing/corrupted tables)
• Permission problems (insufficient access rights)
• ETL pipeline failures (recent data load issues)
• Configuration issues (incorrect database connections)

📝 **Troubleshooting Steps:**
1. **Expand Date Range**: Try last 90-180 days instead of 30
2. **Simplify Filters**: Remove all except essential organization filter
3. **Check Data Sources**: Verify source table accessibility and recent data loads
4. **Test Permissions**: Try with admin/elevated credentials
5. **Review ETL Status**: Check data pipeline health and job logs

💡 **Quick SQL Test:**
```sql
SELECT COUNT(*) FROM your_table 
WHERE date_col >= DATEADD(month, -6, GETDATE())
```

Would you like me to create a support ticket for detailed CDM Workbench assistance?"""
    
    # Default response
    return f"""I can help you with your query: "{message}"

For {org_name}, I can assist with:
• Technical support and troubleshooting
• Software versions and updates
• Configuration and setup
• CDM Workbench issues
• Integration support

Please provide more specific details about your question, or I can create a support ticket for personalized assistance."""

@router.post("/", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message to the chatbot"""
    try:
        # Store user message in history
        user_history = ChatHistory(
            user_id=message.user_id,
            role="user",
            message=message.message,
            timestamp=datetime.utcnow()
        )
        
        if message.user_id not in chat_histories:
            chat_histories[message.user_id] = []
        chat_histories[message.user_id].append(user_history)
        
        # Process the message with intelligent system
        response_text = await get_intelligent_response(
            message.message, 
            message.user_id, 
            message.organization_data
        )
        
        # Store bot response in history
        bot_history = ChatHistory(
            user_id=message.user_id,
            role="assistant",
            message=response_text,
            timestamp=datetime.utcnow()
        )
        chat_histories[message.user_id].append(bot_history)
        
        # Check if response suggests ticket creation
        show_ticket_form = any(phrase in response_text.lower() for phrase in [
            "create a ticket", "support ticket", "escalate", "contact support"
        ])
        
        return ChatResponse(
            response=response_text,
            show_ticket_form=show_ticket_form,
            suggested_actions=["Ask another question", "Create support ticket"] if not show_ticket_form else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/history/{user_id}", response_model=List[ChatHistory])
async def get_chat_history(user_id: str):
    """Get chat history for a user"""
    try:
        history = chat_histories.get(user_id, [])
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@router.post("/initialize")
async def initialize_processor(request: InitializeRequest):
    """Initialize the query processor for a user"""
    try:
        # Extract user info from organization data
        org_data = request.organization_data
        user_id = org_data.get('email', 'demo_user')
        
        # Initialize intelligent processor for user
        if INTELLIGENT_PROCESSOR_AVAILABLE:
            if user_id not in intelligent_processors:
                config = Config()
                intelligent_processors[user_id] = nQuiryProcessor(config)
                print(f"🧠 Initialized intelligent processor for user: {user_id}")
        
        
        # Initialize empty chat history
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        return {
            "status": "initialized",
            "user_id": user_id,
            "organization": org_data.get('name', 'Unknown'),
            "message": "nQuiry is ready to assist you!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing processor: {str(e)}")

@router.delete("/history/{user_id}")
async def clear_chat_history(user_id: str):
    """Clear chat history for a user"""
    try:
        if user_id in chat_histories:
            chat_histories[user_id] = []
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")