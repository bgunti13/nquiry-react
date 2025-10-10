"""
FastAPI server for nQuiry - Uses existing intelligent system
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import asyncio
import os

# Import your existing intelligent system
from main import IntelligentQueryProcessor
from chat_history_manager import ChatHistoryManager

app = FastAPI(title="nQuiry API", version="1.0.0")


def get_ist_time():
    """Get current time in IST (Indian Standard Time)"""
    # Get current UTC time and add IST offset (5 hours 30 minutes)
    utc_now = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = utc_now + ist_offset
    # Return as naive datetime (without timezone info) so frontend treats it correctly
    return ist_time

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: str
    organization_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    show_ticket_form: bool = False
    ticket_query: Optional[str] = None
    is_escalation: Optional[bool] = None

class InitializeRequest(BaseModel):
    customer_email: str

# Initialize MongoDB chat history manager
try:
    chat_history_manager = ChatHistoryManager()
    print("✅ Connected to MongoDB for chat history")
except Exception as e:
    print(f"⚠️ MongoDB connection failed: {e}")
    print("⚠️ Using fallback in-memory storage")
    chat_history_manager = None


def is_greeting_message(message: str) -> tuple:
    """Use LLM to detect if message is a greeting and generate appropriate response"""
    # First, simple fallback check for common greetings
    message_lower = message.lower().strip()
    simple_greetings = [
        'hi', 'hello', 'hey', 'hiya', 'howdy', 'greetings', 'good morning', 
        'good afternoon', 'good evening', 'hey there', 'hi there', 'hello there'
    ]
    
    # Check if message is exactly a simple greeting (or with punctuation)
    clean_message = message_lower.rstrip('!.,?').strip()
    if clean_message in simple_greetings:
        greeting_response = """Hello! 👋 Welcome to nQuiry, your intelligent query and support assistant. 

I'm here to help you with:
• Technical questions and troubleshooting
• System configuration issues  
• Documentation searches
• Support ticket creation when needed

Feel free to ask me about any issues you're experiencing or questions about our systems. How can I assist you today?"""
        return True, greeting_response
    
    # If not a simple greeting, try LLM detection for more complex cases
    try:
        import boto3
        import json
        from config import AWS_REGION, BEDROCK_MODEL
        
        # Create Bedrock client
        session = boto3.Session(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=AWS_REGION
        )
        bedrock_client = session.client('bedrock-runtime')
        
        prompt = f"""
You are an AI assistant for nQuiry, an intelligent query and support system. 

Analyze this user message: "{message}"

Task 1: Determine if this is a greeting message (like "hi", "hello", "good morning", "hey there", etc.)

Task 2: If it IS a greeting, generate a friendly, professional welcome response that:
- Welcomes them to nQuiry
- Briefly explains that you're here to help with technical questions and support
- Encourages them to ask about any issues or questions they have
- Keeps the tone warm but professional

Task 3: If it's NOT a greeting, just respond with "NOT_GREETING"

Format your response as JSON:
{{
  "is_greeting": true/false,
  "response": "your generated greeting response or NOT_GREETING"
}}

Examples of greetings: hi, hello, hey, good morning, good afternoon, howdy, greetings, etc.
Examples of non-greetings: "how to configure SFDC", "I have an issue with sync", "what is Model N", etc.
"""

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps(body),
            contentType='application/json'
        )

        response_body = json.loads(response['body'].read())
        llm_response = response_body['content'][0]['text']
        
        # Parse JSON response
        try:
            parsed_response = json.loads(llm_response)
            is_greeting = parsed_response.get('is_greeting', False)
            greeting_response = parsed_response.get('response', '')
            
            if is_greeting and greeting_response != "NOT_GREETING":
                return True, greeting_response
            else:
                return False, ""
                
        except json.JSONDecodeError:
            # Fallback: try to extract from text response
            if 'true' in llm_response.lower() and 'greeting' in llm_response.lower():
                # Extract response text (basic fallback)
                lines = llm_response.split('\n')
                for line in lines:
                    if 'response' in line.lower() and len(line.strip()) > 20:
                        return True, line.split(':', 1)[1].strip().strip('"')
            return False, ""
            
    except Exception as e:
        print(f"⚠️ Error in LLM greeting detection: {e}")
        # Final fallback - return False to continue with normal processing
        return False, ""


def is_satisfaction_response(message: str) -> tuple:
    """Detect if user is indicating they're satisfied or don't need more help"""
    message_lower = message.lower().strip()
    
    # Common satisfaction/completion phrases
    satisfaction_phrases = [
        'no', 'nope', 'no thanks', 'no thank you', 'that\'s it', 'thats it',
        'i\'m good', 'im good', 'all good', 'that\'s all', 'thats all',
        'nothing else', 'no more help', 'i\'m satisfied', 'im satisfied',
        'that helps', 'that\'s helpful', 'thats helpful', 'perfect',
        'thank you', 'thanks', 'appreciate it', 'that works',
        'no further assistance', 'no additional help', 'that\'s enough',
        'thats enough', 'all set', 'we\'re good', 'were good'
    ]
    
    # Check for exact matches or close matches
    clean_message = message_lower.rstrip('!.,?').strip()
    
    # Direct satisfaction indicators
    if clean_message in satisfaction_phrases:
        closing_response = """Thank you for using Nquiry! 🙏 

I'm glad I could assist you today. If you need any help in the future, please don't hesitate to reach out. 

Have a great day! 👋"""
        return True, closing_response
    
    # Check for longer responses that contain satisfaction indicators
    if any(phrase in clean_message for phrase in ['no thanks', 'no thank you', 'that\'s all', 'nothing else', 'i\'m good', 'all good']):
        closing_response = """Thank you for using nQuiry! 🙏 

I'm glad I could help resolve your query. If you have any other questions or need assistance in the future, feel free to ask anytime.

Have a wonderful day! 👋"""
        return True, closing_response
    
    return False, ""


def is_direct_ticket_request(query):
    """Check if the user is directly requesting to create a ticket or escalate to human support"""
    query_lower = query.lower().strip()
    
    # Direct ticket creation keywords
    ticket_keywords = [
        'create a ticket', 'create ticket', 'make a ticket', 'make ticket',
        'open a ticket', 'open ticket', 'submit a ticket', 'submit ticket',
        'file a ticket', 'file ticket', 'raise a ticket', 'raise ticket',
        'log a ticket', 'log ticket', 'create support ticket', 'ticket for'
    ]
    
    # Human support escalation keywords (natural language patterns)
    escalation_keywords = [
        'assign it to human support', 'assign to human support', 'escalate to support',
        'escalate to human support', 'escalate to support team', 'need human assistance',
        'need human help', 'transfer to human', 'human support', 'speak to a human',
        'talk to a human', 'contact human support', 'get human help',
        'assign to support team', 'escalate this issue', 'escalate this to support',
        'forward to support', 'send to support team', 'human intervention needed',
        'need manual assistance', 'require human support', 'human review needed',
        'assign for further investigation', 'human support for further investigation'
    ]
    
    # Check for any matching keywords
    all_keywords = ticket_keywords + escalation_keywords
    return any(keyword in query_lower for keyword in all_keywords)


def extract_issue_from_ticket_request(query):
    """Extract the actual issue from a ticket creation request"""
    query_lower = query.lower().strip()
    
    # Common patterns to extract the issue
    patterns = [
        r'create.*?ticket.*?for\s+(.*)',
        r'make.*?ticket.*?for\s+(.*)',
        r'open.*?ticket.*?for\s+(.*)',
        r'submit.*?ticket.*?for\s+(.*)',
        r'file.*?ticket.*?for\s+(.*)',
        r'raise.*?ticket.*?for\s+(.*)',
        r'log.*?ticket.*?for\s+(.*)',
        r'ticket.*?for\s+(.*)',
        r'create.*?ticket.*?about\s+(.*)',
        r'ticket.*?about\s+(.*)'
    ]
    
    import re
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            issue = match.group(1).strip()
            # Clean up the extracted issue
            issue = issue.replace('the ', '').replace('my ', '').replace('our ', '')
            return issue.strip()
    
    # If no pattern matches, return the original query
    return query


# In-memory storage for processors and fallback history
processors = {}
chat_histories = {}  # Fallback if MongoDB is not available

def create_processor_for_user(customer_email: str):
    """Create an IntelligentQueryProcessor for a specific user without prompting for email"""
    
    # Create a custom initialization that bypasses the email prompt
    # We'll monkey-patch the MindTouchTool.get_customer_email_from_input method temporarily
    from tools.mindtouch_tool import MindTouchTool
    
    # Store original method
    original_get_email = MindTouchTool.get_customer_email_from_input
    
    # Replace with our email
    MindTouchTool.get_customer_email_from_input = lambda: customer_email
    
    try:
        # Create processor in streamlit mode (which should skip prompts)
        processor = IntelligentQueryProcessor(customer_email=customer_email, streamlit_mode=True)
        return processor
    finally:
        # Restore original method
        MindTouchTool.get_customer_email_from_input = original_get_email

@app.post("/api/chat/initialize")
async def initialize_processor(request: InitializeRequest):
    """Initialize the query processor for a user"""
    try:
        customer_email = request.customer_email
        
        # Just get organization data using the customer email (no processor initialization yet)
        from tools.mindtouch_tool import MindTouchTool
        try:
            mindtouch_tool = MindTouchTool(customer_email=customer_email)
            org_data = mindtouch_tool.get_customer_info()
        except Exception as e:
            print(f"⚠️  Warning: Could not get customer info: {e}")
            # Fallback organization data
            org_data = {
                'email': customer_email,
                'organization': 'Unknown',
                'role': 'Unknown', 
                'available_roles': [],
                'domain': customer_email.split('@')[1] if '@' in customer_email else None,
                'dynamic_mapping': False
            }
        
        # Store the customer info for later processor initialization
        processors[customer_email] = {
            'customer_email': customer_email,
            'org_data': org_data,
            'processor': None  # Will be initialized when first message is sent
        }
        
        print(f"✅ Prepared nQuiry initialization for {customer_email} ({org_data.get('organization')})")
        
        return {
            "status": "initialized",
            "user_id": customer_email,
            "organization_data": org_data,
            "message": f"nQuiry is ready to assist {org_data.get('organization')}!"
        }
        
    except Exception as e:
        print(f"❌ Error initializing processor: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing processor: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message to the intelligent chatbot"""
    try:
        user_id = message.user_id
        
        # Check if user is initialized, if not auto-initialize
        if user_id not in processors:
            print(f"⚠️ User {user_id} not initialized, auto-initializing...")
            
            # Auto-initialize the user
            from tools.mindtouch_tool import MindTouchTool
            try:
                mindtouch_tool = MindTouchTool(customer_email=user_id)
                org_data = mindtouch_tool.get_customer_info()
            except Exception as e:
                print(f"⚠️ Warning: Could not get customer info for auto-initialization: {e}")
                # Fallback organization data
                org_data = {
                    'email': user_id,
                    'organization': 'Unknown',
                    'role': 'Unknown', 
                    'available_roles': [],
                    'domain': user_id.split('@')[1] if '@' in user_id else None,
                    'dynamic_mapping': False
                }
            
            # Store the customer info for processor initialization
            processors[user_id] = {
                'customer_email': user_id,
                'org_data': org_data,
                'processor': None  # Will be initialized below
            }
            
            print(f"✅ Auto-initialized user {user_id} ({org_data.get('organization')})")
        
        user_data = processors[user_id]
        
        # Initialize the actual processor if not done yet
        if user_data['processor'] is None:
            print(f"🧠 Creating IntelligentQueryProcessor for {user_id}...")
            # Create a custom processor that doesn't prompt for email
            processor = create_processor_for_user(user_data['customer_email'])
            user_data['processor'] = processor
        
        processor = user_data['processor']
        
        # Store message in history (MongoDB or fallback)
        if chat_history_manager:
            chat_history_manager.add_message(user_id, "user", message.message, message.session_id)
            # Get history from MongoDB for context
            history = chat_history_manager.get_history(user_id)
        else:
            # Fallback to in-memory storage
            if user_id not in chat_histories:
                chat_histories[user_id] = []
            chat_histories[user_id].append({
                "role": "user",
                "message": message.message,
                "timestamp": get_ist_time()
            })
            history = chat_histories.get(user_id, [])

        # Process with the real nQuiry intelligent system
        print(f"🧠 Processing with IntelligentQueryProcessor: '{message.message}'")
        
        # Check if this is a greeting message first
        print(f"🔍 Checking if '{message.message}' is a greeting...")
        is_greeting, greeting_response = is_greeting_message(message.message)
        print(f"🔍 Greeting check result: is_greeting={is_greeting}")
        
        if is_greeting:
            print(f"👋 Greeting detected, responding with: {greeting_response[:50]}...")
            
            # Store bot response in history
            if chat_history_manager:
                chat_history_manager.add_message(user_id, "assistant", greeting_response, message.session_id)
            else:
                chat_histories[user_id].append({
                    "role": "assistant", 
                    "message": greeting_response,
                    "timestamp": get_ist_time()
                })
            
            return ChatResponse(
                response=greeting_response,
                show_ticket_form=False
            )
        
        # Check if user is indicating satisfaction/completion
        print(f"🔍 Checking if '{message.message}' indicates satisfaction...")
        is_satisfied, satisfaction_response = is_satisfaction_response(message.message)
        print(f"🔍 Satisfaction check result: is_satisfied={is_satisfied}")
        
        if is_satisfied:
            print(f"✅ User satisfaction detected, sending closing message...")
            
            # Store bot response in history
            if chat_history_manager:
                chat_history_manager.add_message(user_id, "assistant", satisfaction_response, message.session_id)
            else:
                chat_histories[user_id].append({
                    "role": "assistant", 
                    "message": satisfaction_response,
                    "timestamp": get_ist_time()
                })
            
            return ChatResponse(
                response=satisfaction_response,
                show_ticket_form=False
            )
        
        show_ticket = False  # Initialize ticket flag
        
        # Convert MongoDB history format to the format expected by IntelligentQueryProcessor
        processed_history = []
        if history:
            for msg in history:
                if isinstance(msg, dict):
                    # Handle MongoDB format
                    if 'role' in msg and 'content' in msg:
                        processed_history.append({
                            'role': msg['role'],
                            'message': msg['content'],
                            'timestamp': msg.get('timestamp')
                        })
                    elif 'role' in msg and 'message' in msg:
                        processed_history.append(msg)
                    # Handle fallback format
                    elif 'type' in msg:
                        processed_history.append({
                            'role': msg['type'],  # 'user' or 'assistant'
                            'message': msg['message'],
                            'timestamp': msg.get('timestamp')
                        })
        
        # Check if user is responding positively to a ticket creation suggestion
        if processed_history and len(processed_history) > 0:
            last_bot_message = None
            for msg in reversed(processed_history):
                if msg.get('role') == 'assistant':
                    last_bot_message = msg.get('message', '')
                    break
            
            # Check if the last bot message asked about creating a ticket
            if last_bot_message and any(phrase in last_bot_message.lower() for phrase in [
                'would you like me to create a support ticket',
                'would you like to create a ticket',
                'create a support ticket',
                'should i create a ticket'
            ]):
                # Check if current user message is affirmative
                user_message_lower = message.message.lower().strip()
                affirmative_responses = [
                    'yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'please', 'go ahead',
                    'create ticket', 'create a ticket', 'yes please', 'yes, please',
                    'proceed', 'continue', 'that would be great', 'sounds good'
                ]
                
                if any(response in user_message_lower for response in affirmative_responses):
                    print(f"🎫 User confirmed ticket creation with: '{message.message}'")
                    # Extract the original issue from conversation history for ticket creation
                    original_query = "Support assistance requested"
                    for msg in processed_history:
                        if msg.get('role') == 'user' and len(msg.get('message', '')) > 10:
                            original_query = msg.get('message', original_query)
                            break
                    
                    # Show ticket form immediately since user confirmed
                    return ChatResponse(
                        response=f"Perfect! I'll help you create a support ticket. Please provide the required details below.",
                        show_ticket_form=True,
                        ticket_query=original_query,
                        is_escalation=False
                    )
                
                # Check if user declined ticket creation
                negative_responses = [
                    'no', 'nope', 'no thanks', 'no thank you', 'not now', 'maybe later',
                    'i\'m good', 'im good', 'that\'s fine', 'thats fine', 'all good',
                    'no need', 'not necessary', 'i\'ll manage', 'ill manage'
                ]
                
                if any(response in user_message_lower for response in negative_responses):
                    print(f"❌ User declined ticket creation with: '{message.message}'")
                    
                    # Store the decline response in history
                    decline_response = """No problem! 👍 

I'm glad the information I provided was helpful. If you need any assistance in the future or have other questions, please don't hesitate to ask.

Is there anything else I can help you with today?"""
                    
                    if chat_history_manager:
                        chat_history_manager.add_message(user_id, "assistant", decline_response, message.session_id)
                    else:
                        chat_histories[user_id].append({
                            "role": "assistant", 
                            "message": decline_response,
                            "timestamp": get_ist_time()
                        })
                    
                    return ChatResponse(
                        response=decline_response,
                        show_ticket_form=False
                    )

        # First check if this is a direct ticket creation request (like Streamlit does)
        if is_direct_ticket_request(message.message):
            print(f"🎫 Direct ticket creation request detected for: '{message.message}'")
            
            # Check if this is an escalation request (should auto-create ticket)
            query_lower = message.message.lower().strip()
            escalation_phrases = [
                'assign it to human support', 'assign to human support', 'escalate to support',
                'escalate to human support', 'escalate to support team', 'need human assistance',
                'need human help', 'transfer to human', 'human support', 'speak to a human',
                'talk to a human', 'contact human support', 'get human help',
                'assign to support team', 'escalate this issue', 'escalate this to support',
                'forward to support', 'send to support team', 'human intervention needed',
                'need manual assistance', 'require human support', 'human review needed',
                'assign for further investigation', 'human support for further investigation'
            ]
            
            is_escalation = any(phrase in query_lower for phrase in escalation_phrases)
            actual_issue = extract_issue_from_ticket_request(message.message)
            
            if is_escalation:
                # For escalation requests, ask for confirmation first
                response_text = f"🎫 **Escalating to Human Support**\n\nI understand you need human assistance with: {actual_issue}\n\nWould you like me to create a support ticket to escalate this to our support team?"
                show_ticket = False
            else:
                # For explicit ticket creation requests, show the form directly
                print(f"🎫 User explicitly requested ticket creation, showing form directly")
                
                # Store the request acknowledgment in history
                acknowledgment = f"Perfect! I'll help you create a support ticket for: {actual_issue}\n\nPlease provide the required details below."
                
                if chat_history_manager:
                    chat_history_manager.add_message(user_id, "assistant", acknowledgment, message.session_id)
                else:
                    if user_id not in chat_histories:
                        chat_histories[user_id] = []
                    chat_histories[user_id].append({
                        "role": "assistant", 
                        "message": acknowledgment,
                        "timestamp": get_ist_time()
                    })
                
                return ChatResponse(
                    response=acknowledgment,
                    show_ticket_form=True,
                    ticket_query=actual_issue,
                    is_escalation=False
                )
        else:
            # If not a direct ticket request, process through intelligent search flow
            print(f"📚 Query '{message.message}' -> Using intelligent search flow: JIRA → MindTouch → Comprehensive Response → Ticket Option")
            try:
                # Always use process_query method which handles the proper JIRA → MindTouch → Bedrock → Ticket flow
                print("🔍 Using intelligent search flow: JIRA → MindTouch → Comprehensive Response → Ticket Option")
                result = processor.process_query(user_id, message.message, processed_history)
                
                if result and isinstance(result, dict):
                    # Handle process_query result
                    if 'formatted_response' in result:
                        response_text = result['formatted_response']
                    elif 'response' in result:
                        response_text = result['response']
                    else:
                        response_text = str(result)
                    
                    # Check if this is a ticket creation flow or if ticket was created
                    if result.get('ticket_created'):
                        # Ticket was actually created - don't show form
                        response_text = result.get('ticket_created', response_text)
                        show_ticket = False
                    else:
                        # Don't auto-show ticket form - wait for user to explicitly request it
                        # The response already asks if they want to create a ticket
                        show_ticket = False
                elif result:
                    response_text = str(result)
                else:
                    response_text = "I apologize, but I couldn't find relevant information for your query. Would you like me to create a support ticket to get this resolved?"
                    # Don't auto-show form, wait for confirmation
                    show_ticket = False
                    
            except Exception as e:
                print(f"⚠️ Error in intelligent processing: {e}")
                org_name = user_data['org_data'].get('organization', 'your organization')
                response_text = f"I encountered an issue while searching our knowledge base for {org_name}. Would you like me to create a support ticket to ensure your question gets properly addressed?"
                # Don't auto-show form, wait for confirmation
                show_ticket = False
        
        # Store bot response in history (MongoDB or fallback)
        if chat_history_manager:
            chat_history_manager.add_message(user_id, "assistant", response_text, message.session_id)
        else:
            # Fallback to in-memory storage
            chat_histories[user_id].append({
                "role": "assistant", 
                "message": response_text,
                "timestamp": get_ist_time()
            })
        
        return ChatResponse(
            response=response_text,
            show_ticket_form=show_ticket
        )
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str):
    """Get chat history for a user from MongoDB or fallback storage"""
    try:
        print(f"🔍 Getting chat history for user: {user_id}")
        
        if chat_history_manager:
            # Get from MongoDB
            print(f"📊 Fetching from MongoDB for user: {user_id}")
            history = chat_history_manager.get_history(user_id)
            print(f"📋 MongoDB returned {len(history) if history else 0} items for user: {user_id}")
        else:
            # Fallback to in-memory storage
            print(f"💾 Using fallback storage for user: {user_id}")
            history = chat_histories.get(user_id, [])
            print(f"📋 Fallback storage returned {len(history)} items for user: {user_id}")
        
        result = {"history": history}
        print(f"✅ Returning chat history for user {user_id}: {len(history) if history else 0} items")
        return result
    except Exception as e:
        print(f"❌ Error getting chat history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")

@app.delete("/api/chat/history/{user_id}")
async def clear_chat_history(user_id: str):
    """Clear chat history for a user from MongoDB or fallback storage"""
    try:
        if chat_history_manager:
            # Clear from MongoDB
            chat_history_manager.clear_history(user_id)
        else:
            # Clear from in-memory storage
            if user_id in chat_histories:
                chat_histories[user_id] = []
        
        return {"message": "Chat history cleared"}
    except Exception as e:
        print(f"❌ Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")

@app.get("/")
async def root():
    return {"message": "nQuiry FastAPI server is running", "status": "active"}

@app.get("/api/debug/llm-status")
async def llm_status():
    """Debug endpoint to check LLM and service status"""
    try:
        status = {
            "mongodb_connected": chat_history_manager is not None,
            "processors_initialized": len(processors),
            "active_users": list(processors.keys()) if processors else [],
            "services": {
                "aws_bedrock": "Configured (will be available when processor initializes)",
                "mindtouch_llm": "Configured",
                "jira_search": "Configured",
                "chat_history": "MongoDB" if chat_history_manager else "In-Memory"
            }
        }
        return status
    except Exception as e:
        return {
            "error": f"Error getting status: {str(e)}",
            "mongodb_connected": chat_history_manager is not None,
            "processors_initialized": 0
        }

# Pydantic models for ticket creation
class TicketRequest(BaseModel):
    original_query: str
    customer_email: str
    is_escalation: bool = False
    # Allow any additional fields dynamically
    class Config:
        extra = "allow"

@app.post("/api/tickets/create")
async def create_ticket(ticket_request: TicketRequest):
    """Create a support ticket"""
    try:
        # Import the ticket creator
        from ticket_creator import TicketCreator
        
        # Create ticket creator instance
        ticket_creator = TicketCreator()
        
        # Convert the request to a dictionary to handle dynamic fields
        request_dict = ticket_request.dict()
        
        # Extract base fields
        query = request_dict.pop('original_query')
        customer_email = request_dict.pop('customer_email')
        is_escalation = request_dict.pop('is_escalation', False)
        
        # All remaining fields are form data
        form_data = request_dict
        form_data['is_escalation'] = is_escalation
        
        # Create the ticket
        ticket_result = ticket_creator.create_ticket_streamlit(
            query=query,
            customer_email=customer_email,
            form_data=form_data
        )
        
        # Generate proper JIRA ticket ID if not provided
        if not ticket_result.get('jira_ticket_id') or ticket_result.get('jira_ticket_id') == 'N/A':
            category = ticket_result.get('category', 'GENERAL')
            # Generate JIRA ticket ID: PROJECT-XXXXX (5 digit random number)
            import random
            random_number = random.randint(10000, 99999)
            jira_ticket_id = f"{category}-{random_number}"
            ticket_result['jira_ticket_id'] = jira_ticket_id
            print(f"✅ Generated JIRA ticket ID: {jira_ticket_id}")
        
        # Generate ticket content for download
        ticket_content = f"""NQUIRY SUPPORT TICKET
========================

Ticket ID: {ticket_result.get('ticket_id', 'N/A')}
JIRA Ticket: {ticket_result.get('jira_ticket_id', 'N/A')}
Category: {ticket_result.get('category', 'N/A')}
Customer: {ticket_result.get('customer', 'N/A')}
Customer Email: {ticket_result.get('customer_email', 'N/A')}
Created: {ticket_result.get('created_date', 'N/A')}

ORIGINAL QUERY:
===============
{ticket_result.get('original_query', 'N/A')}

TICKET DETAILS:
===============
Priority: {ticket_result.get('priority', 'N/A')}
Area Affected: {ticket_result.get('area_affected', 'N/A')}
Version Affected: {ticket_result.get('version_affected', 'N/A')}
Environment: {ticket_result.get('environment', 'N/A')}
Description: {ticket_result.get('description', 'N/A')}
Escalation: {ticket_result.get('is_escalation', False)}

ADDITIONAL FIELDS:
==================
"""
        
        # Add any additional fields
        for key, value in ticket_result.items():
            if key not in ['ticket_id', 'jira_ticket_id', 'category', 'customer', 'customer_email', 
                          'created_date', 'original_query', 'priority', 'area_affected', 
                          'version_affected', 'environment', 'description', 'is_escalation']:
                ticket_content += f"{key.replace('_', ' ').title()}: {value}\n"
        
        # Add follow-up message to chat history
        if chat_history_manager and customer_email:
            follow_up_message = "Ticket created successfully! 🎫\n\nYour support request has been submitted and our team will review it shortly. You should receive updates via email.\n\nIs there anything else I can help you with today?"
            print(f"✅ Adding follow-up message to chat history for {customer_email}")
            chat_history_manager.add_message(customer_email, "assistant", follow_up_message, None)
            print(f"✅ Follow-up message added successfully")
            
            # Also add to in-memory storage as backup
            if customer_email not in chat_histories:
                chat_histories[customer_email] = []
            chat_histories[customer_email].append({
                "role": "assistant",
                "message": follow_up_message,
                "timestamp": get_ist_time()
            })
        else:
            print(f"⚠️ Could not add follow-up message - chat_history_manager: {chat_history_manager is not None}, customer_email: {customer_email}")
        
        return {
            "status": "success",
            "message": "Ticket created successfully! 🎫\n\nYour support request has been submitted and our team will review it shortly. You should receive updates via email.\n\nIs there anything else I can help you with today?",
            "refresh_chat": True,  # Signal frontend to refresh chat
            "follow_up_added": True,  # Indicate follow-up message was added
            "ticket_data": {
                "ticket_id": ticket_result.get('ticket_id', 'N/A'),
                "jira_ticket_id": ticket_result.get('jira_ticket_id', 'N/A'),
                "category": ticket_result.get('category', 'N/A'), 
                "customer": ticket_result.get('customer', 'N/A'),
                "customer_email": ticket_result.get('customer_email', 'N/A'),
                "created_date": ticket_result.get('created_date', 'N/A'),
                "priority": ticket_result.get('priority', 'N/A'),
                "area_affected": ticket_result.get('area_affected', 'N/A'),
                "version_affected": ticket_result.get('version_affected', 'N/A'),
                "environment": ticket_result.get('environment', 'N/A'),
                "description": ticket_result.get('description', 'N/A'),
                "is_escalation": ticket_result.get('is_escalation', False)
            },
            "downloadable_content": ticket_content,
            "filename": f"ticket_{ticket_result.get('category', 'UNKNOWN')}_{ticket_result.get('customer', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        }
        
    except Exception as e:
        print(f"❌ Error creating ticket: {e}")
        return {
            "status": "error", 
            "message": f"Failed to create ticket: {str(e)}"
        }

@app.get("/api/chat/transcript/{user_id}")
async def get_chat_transcript(user_id: str):
    """Generate and return chat transcript for download"""
    try:
        # Get chat history
        chat_messages = []
        if chat_history_manager:
            chat_messages = chat_history_manager.get_history(user_id)
        elif user_id in chat_histories:
            chat_messages = chat_histories[user_id]
        
        if not chat_messages:
            return {
                "status": "error",
                "message": "No chat history found"
            }
        
        # Generate transcript content
        transcript_lines = []
        transcript_lines.append("NQUIRY CHAT TRANSCRIPT")
        transcript_lines.append("=" * 50)
        transcript_lines.append("")
        transcript_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        transcript_lines.append(f"User: {user_id}")
        transcript_lines.append(f"Session Messages: {len(chat_messages)}")
        transcript_lines.append("")
        transcript_lines.append("CONVERSATION LOG:")
        transcript_lines.append("-" * 30)
        transcript_lines.append("")
        
        # Add each message
        for i, message in enumerate(chat_messages, 1):
            if isinstance(message, dict):
                role = message.get('role', 'unknown')
                # Handle both 'content' and 'message' fields for compatibility
                content = message.get('content') or message.get('message', '')
                timestamp = message.get('timestamp', '')
                if hasattr(timestamp, 'strftime'):
                    timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = str(timestamp)
            else:
                # Handle different message format
                role = getattr(message, 'role', 'unknown')
                content = getattr(message, 'content', '') or getattr(message, 'message', str(message))
                timestamp = getattr(message, 'timestamp', '')
            
            if role == 'user':
                transcript_lines.append(f"[{timestamp}] 👤 USER:")
                transcript_lines.append(f"    {content}")
            elif role == 'assistant':
                transcript_lines.append(f"[{timestamp}] 🤖 NQUIRY:")
                # Clean content of markdown for plain text
                import re
                clean_content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Remove bold
                clean_content = re.sub(r'\*([^*]+)\*', r'\1', clean_content)  # Remove italic
                clean_content = re.sub(r'#{1,6}\s?', '', clean_content)  # Remove headers
                clean_content = re.sub(r'`([^`]+)`', r'\1', clean_content)  # Remove code formatting
                
                # Split long responses into multiple lines for readability
                lines = clean_content.split('\n')
                for line in lines:
                    if line.strip():
                        transcript_lines.append(f"    {line.strip()}")
            
            transcript_lines.append("")  # Empty line between messages
        
        transcript_content = '\n'.join(transcript_lines)
        filename = f"chat_transcript_{user_id.replace('@', '_at_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return {
            "status": "success",
            "content": transcript_content,
            "filename": filename
        }
        
    except Exception as e:
        print(f"❌ Error generating chat transcript: {e}")
        return {
            "status": "error",
            "message": f"Failed to generate transcript: {str(e)}"
        }

@app.get("/api/tickets/fields/{category}")
async def get_ticket_fields(category: str):
    """Get required and populated fields for a specific ticket category"""
    try:
        from ticket_creator import TicketCreator
        
        ticket_creator = TicketCreator()
        
        # Get category configuration
        categories = ticket_creator.ticket_config.get("ticket_categories", {})
        if category.upper() not in categories:
            return {
                "status": "error",
                "message": f"Unknown category: {category}"
            }
        
        category_config = categories[category.upper()]
        
        return {
            "status": "success",
            "category": category.upper(),
            "required_fields": category_config.get("required_fields", {}),
            "populated_fields": category_config.get("populated_fields", {}),
            "keywords": category_config.get("keywords", [])
        }
        
    except Exception as e:
        print(f"❌ Error getting ticket fields: {e}")
        return {
            "status": "error",
            "message": f"Failed to get ticket fields: {str(e)}"
        }


@app.post("/api/tickets/follow-up")
async def ticket_follow_up(request: dict):
    """Add follow-up message after ticket creation"""
    try:
        user_id = request.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        follow_up_message = "Ticket created successfully! 🎫\n\nYour support request has been submitted and our team will review it shortly. You should receive updates via email.\n\nIs there anything else I can help you with today?"
        
        # Add to chat history
        if chat_history_manager:
            chat_history_manager.add_message(user_id, "assistant", follow_up_message, None)
        else:
            # Fallback to in-memory storage
            if user_id not in chat_histories:
                chat_histories[user_id] = []
        chat_histories[user_id].append({
            "role": "assistant",
            "message": follow_up_message,
            "timestamp": get_ist_time()
        })
        
        return {"status": "success", "message": "Follow-up message added"}
        
    except Exception as e:
        print(f"❌ Error adding follow-up message: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding follow-up message: {str(e)}")


@app.post("/api/chat/bot-follow-up")
async def bot_follow_up(request: dict):
    """Send a follow-up message from bot after ticket creation"""
    try:
        user_id = request.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        follow_up_message = "Ticket created successfully! 🎫\n\nYour support request has been submitted and our team will review it shortly. You should receive updates via email.\n\nIs there anything else I can help you with today?"
        
        # Add to both MongoDB and in-memory storage
        if chat_history_manager:
            chat_history_manager.add_message(user_id, "assistant", follow_up_message, None)
        
        # Also add to in-memory as backup
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        chat_histories[user_id].append({
            "role": "assistant",
            "message": follow_up_message,
            "timestamp": get_ist_time()
        })
        
        # Return the message in ChatResponse format so frontend can display it immediately
        return ChatResponse(
            response=follow_up_message,
            show_ticket_form=False
        )
        
    except Exception as e:
        print(f"❌ Error sending bot follow-up: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending bot follow-up: {str(e)}")


@app.post("/api/chat/add-bot-message")
async def add_bot_message(request: dict):
    """Add a bot message to the chat (for follow-ups after ticket creation)"""
    try:
        user_id = request.get('user_id')
        message = request.get('message')
        
        if not user_id or not message:
            raise HTTPException(status_code=400, detail="user_id and message are required")
        
        # Add to chat history
        if chat_history_manager:
            chat_history_manager.add_message(user_id, "assistant", message, None)
        else:
            # Fallback to in-memory storage
            if user_id not in chat_histories:
                chat_histories[user_id] = []
            chat_histories[user_id].append({
                "role": "assistant",
                "message": message,
                "timestamp": get_ist_time()
            })
        
        return {"status": "success", "message": "Bot message added to chat"}
        
    except Exception as e:
        print(f"❌ Error adding bot message: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding bot message: {str(e)}")


@app.get("/api/chat/latest/{user_id}")
async def get_latest_messages(user_id: str, since: Optional[str] = None):
    """Get latest messages for a user, optionally since a specific timestamp"""
    try:
        if chat_history_manager:
            # Get from MongoDB
            history = chat_history_manager.get_history(user_id)
            
            # If since timestamp provided, filter messages
            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                    history = [msg for msg in history if msg.get('timestamp', datetime.min) > since_dt]
                except Exception as e:
                    print(f"⚠️ Error parsing since timestamp: {e}")
            
            return {"status": "success", "messages": history}
        else:
            # Fallback to in-memory storage
            history = chat_histories.get(user_id, [])
            return {"status": "success", "messages": history}
            
    except Exception as e:
        print(f"❌ Error getting latest messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting latest messages: {str(e)}")


@app.post("/api/tickets/preview")
async def preview_ticket_category(request: dict):
    """Preview what ticket category would be determined for a query"""
    try:
        from ticket_creator import TicketCreator
        
        ticket_creator = TicketCreator()
        query = request.get("query", "")
        customer_email = request.get("customer_email", "")
        
        # Extract customer name from email
        customer = "UNKNOWN"
        if customer_email:
            domain = customer_email.split('@')[-1].lower()
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',  
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie'
            }
            customer = domain_to_customer.get(domain, domain.split('.')[0].capitalize())
        
        # Determine category
        category = ticket_creator.determine_ticket_category(query, customer, customer_email)
        
        # Get category configuration
        categories = ticket_creator.ticket_config.get("ticket_categories", {})
        category_config = categories.get(category, {})
        
        return {
            "status": "success",
            "category": category,
            "customer": customer,
            "required_fields": category_config.get("required_fields", {}),
            "populated_fields": category_config.get("populated_fields", {}),
            "keywords": category_config.get("keywords", [])
        }
        
    except Exception as e:
        print(f"❌ Error previewing ticket category: {e}")
        return {
            "status": "error",
            "message": f"Failed to preview ticket category: {str(e)}"
        }

@app.post("/api/chat/summarize")
async def summarize_conversation(request: dict):
    """Generate a concise summary of a conversation for ticket creation"""
    try:
        from main import IntelligentQueryProcessor
        import json
        
        messages = request.get("messages", [])
        query = request.get("query", "")
        
        if not messages:
            return {
                "status": "success",
                "summary": query or "No conversation to summarize"
            }
        
        # Format conversation for LLM analysis
        conversation_text = ""
        for msg in messages:
            role = "User" if msg.get("type") == "user" else "Assistant"
            content = msg.get("content", "")
            conversation_text += f"{role}: {content}\n\n"
        
        # Use AWS Bedrock to summarize the conversation
        processor = IntelligentQueryProcessor(customer_email="demo@example.com", streamlit_mode=True)
        bedrock_client = processor.response_formatter.bedrock_client
        model_id = processor.response_formatter.model_id
        
        prompt = f"""Please provide a concise, professional summary of this customer support conversation for a support ticket. 

Focus on:
1. The main issue or question raised
2. Key technical details mentioned
3. Any troubleshooting steps attempted
4. The current status/next steps needed

Keep it under 200 words and use clear, technical language suitable for support staff.

Conversation:
{conversation_text}

Current query: {query}

Summary:"""

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and len(response_body['content']) > 0:
            summary = response_body['content'][0]['text'].strip()
            
            return {
                "status": "success",
                "summary": summary
            }
        else:
            # Fallback to simple summary
            return {
                "status": "success",
                "summary": f"Customer inquiry: {query}\n\nConversation involved {len(messages)} messages discussing technical support requirements."
            }
            
    except Exception as e:
        print(f"❌ Error summarizing conversation: {e}")
        # Fallback to simple summary
        messages = request.get("messages", [])
        query = request.get("query", "")
        
        return {
            "status": "success",
            "summary": f"Customer inquiry: {query}\n\nConversation involved {len(messages)} messages. Please review the full conversation history for complete context."
        }

@app.get("/api/tickets/recent/{organization}")
async def get_recent_tickets(organization: str):
    """Get recent JIRA tickets for a specific organization"""
    try:
        # Import JIRA search functionality
        from main import IntelligentQueryProcessor
        
        # Create a processor to access JIRA functionality
        processor = IntelligentQueryProcessor(customer_email="dummy@example.com", streamlit_mode=True)
        
        # Map organization names to domain patterns for JIRA search
        org_domain_map = {
            'Novartis': 'novartis.com',
            'AMD': 'amd.com', 
            'WDC': 'wdc.com',
            'Abbott': 'abbott.com',
            'AbbVie': 'abbvie.com',
            'Amgen': 'amgen.com'
        }
        
        # Get the domain for the organization
        domain = org_domain_map.get(organization, None)
        if not domain:
            print(f"⚠️ Unknown organization: {organization}")
            return {"tickets": []}
        
        # Search for recent tickets from this organization
        print(f"🔍 Getting recent {organization} tickets")
        
        # Use the new get_recent_tickets method
        from ticket_creator import TicketCreator
        ticket_creator = TicketCreator()
        
        # Get recent tickets using the new method
        tickets = ticket_creator.get_recent_tickets(organization, limit=10)
        
        print(f"✅ Found {len(tickets)} recent tickets for {organization}")
        
        # Transform JIRA ticket format to frontend expected format
        transformed_tickets = []
        for ticket in tickets:
            try:
                transformed_ticket = {
                    "id": ticket.get("key", "Unknown"),
                    "title": ticket.get("summary", "No title"),
                    "status": ticket.get("status", "Unknown"),
                    "priority": ticket.get("priority", "Medium"),
                    "created": ticket.get("created", ""),
                    "updated": ticket.get("updated", ""),
                    "assignee": ticket.get("assignee", "Unassigned"),
                    "category": ticket.get("project", organization)  # Use project or fallback to organization
                }
                transformed_tickets.append(transformed_ticket)
            except Exception as e:
                print(f"⚠️ Error transforming ticket {ticket}: {e}")
                continue
        
        print(f"🔄 Transformed {len(transformed_tickets)} tickets for {organization}")
        return {"tickets": transformed_tickets}
        
    except Exception as e:
        print(f"❌ Error fetching recent tickets for {organization}: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty list on error
        return {"tickets": []}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting nQuiry FastAPI server...")
    print("🧠 Using existing intelligent nQuiry system")
    print("🌐 Frontend URL: http://localhost:3000")
    print("📡 API URL: http://localhost:8000") 
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)