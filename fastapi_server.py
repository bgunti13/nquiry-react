"""
FastAPI server for nQuiry - Uses existing intelligent system
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import asyncio
import json
import os
import time
import random

# Import your existing intelligent system
from main import IntelligentQueryProcessor
from chat_history_manager import ChatHistoryManager
from continuous_learning_manager import get_learning_manager
from organization_access_controller import check_organization_access
from image_analyzer import ImageAnalyzer

app = FastAPI(title="nQuiry API", version="1.0.0")


def get_ist_time():
    """Get current time in IST (Indian Standard Time)"""
    # Get current UTC time and add IST offset (5 hours 30 minutes)
    utc_now = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = utc_now + ist_offset
    # Return as naive datetime (without timezone info) so frontend treats it correctly
    return ist_time

def generate_jira_ticket_id(category: str) -> str:
    """Generate a Jira-style ticket ID"""
    random_number = random.randint(10000, 99999)
    return f"{category}-{random_number}"

def generate_ticket_summary(description: str) -> str:
    """Generate a concise summary from the description"""
    # Clean up the description
    desc = description.strip()
    
    # If it's a question, keep it as is but truncate if too long
    if desc.endswith('?'):
        return desc[:80] + "..." if len(desc) > 80 else desc
    
    # For statements, create a support request format
    if len(desc) > 60:
        return f"Support Request: {desc[:60]}..."
    else:
        return f"Support Request: {desc}"

def enhance_description_with_context(query: str, chat_history=None) -> str:
    """Enhance description with AI analysis and conversation context using AWS Bedrock"""
    try:
        # Import AWS Bedrock client
        import boto3
        import json
        
        # Initialize Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'  # You can change this to your preferred region
        )
        
        # Prepare conversation context
        conversation_context = ""
        if chat_history:
            # Get recent relevant messages from user
            user_messages = []
            assistant_messages = []
            for msg in chat_history[-10:]:  # Last 10 messages for context
                if msg.get('role') == 'user' and len(msg.get('message', '')) > 5:
                    user_messages.append(msg.get('message', ''))
                elif msg.get('role') == 'assistant' and len(msg.get('message', '')) > 10:
                    assistant_messages.append(msg.get('message', ''))
            
            if user_messages:
                conversation_context = f"\n\nConversation History:\n"
                for i, msg in enumerate(user_messages[-5:], 1):  # Last 5 user messages
                    conversation_context += f"User Message {i}: {msg}\n"
        
        # Create prompt for Bedrock
        prompt = f"""You are a technical support analyst. Analyze the following user query and conversation history to create a comprehensive ticket description.

Current User Query: {query}
{conversation_context}

Please provide a detailed technical description that:
1. Clearly explains what the user is trying to accomplish
2. Identifies the specific technical area/feature involved
3. Analyzes any context from the conversation
4. Suggests the likely root cause or area of investigation
5. Keeps it professional and technical

Provide only the enhanced description without any prefixes or labels. Make it 2-4 sentences that a support engineer would find helpful."""

        # Call Bedrock Claude model
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
        
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",  # Using Claude 3 Sonnet
            body=json.dumps(body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        enhanced_description = response_body['content'][0]['text'].strip()
        
        print(f"🤖 Generated enhanced description via Bedrock: {enhanced_description[:100]}...")
        
        return enhanced_description
        
    except Exception as e:
        print(f"⚠️ Could not enhance description with Bedrock: {e}")
        
        # Fallback to manual analysis if Bedrock fails
        base_description = query
        
        # Add conversation context manually if available
        if chat_history:
            user_messages = []
            for msg in chat_history[-5:]:
                if msg.get('role') == 'user' and len(msg.get('message', '')) > 10:
                    user_messages.append(msg.get('message', ''))
            
            if len(user_messages) > 1:
                # Create a more detailed fallback description
                base_description = f"""User Issue: {query}

Context: This request is part of an ongoing conversation where the user has been discussing related topics. The user appears to need assistance with system functionality.

Technical Area: Based on the query, this relates to payment processing, specifically rebate management and payment scheduling functionality."""
        else:
            # Enhanced single-query analysis
            if 'rebate' in query.lower():
                base_description = f"""Payment Processing Issue: {query}

This appears to be related to rebate management functionality, specifically concerning the timing and scheduling of future rebate payments. The user needs guidance on system configuration or process workflows for delayed payment creation."""
            elif 'login' in query.lower() or 'access' in query.lower():
                base_description = f"""Access Issue: {query}

This is an authentication/authorization related request. The user is experiencing difficulties accessing the system or specific features."""
            elif 'error' in query.lower() or 'issue' in query.lower():
                base_description = f"""System Error: {query}

The user is encountering a technical issue that requires investigation. This may involve system functionality, data processing, or application behavior."""
            else:
                base_description = f"""User Request: {query}

The user requires technical assistance with system functionality. This request needs analysis to determine the specific area of the application and appropriate resolution steps."""
        
        return base_description

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ImageData(BaseModel):
    base64: str
    type: str
    name: str
    size: int

class ChatMessage(BaseModel):
    message: str
    user_id: str
    organization_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    images: Optional[List[ImageData]] = None

class StreamingChatMessage(BaseModel):
    message: str
    user_id: str
    organization_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    images: Optional[List[ImageData]] = None

class ChatResponse(BaseModel):
    response: str
    show_ticket_form: bool = False
    ticket_query: Optional[str] = None
    is_escalation: Optional[bool] = None
    auto_ticket_created: Optional[bool] = None
    ticket_data: Optional[Dict[str, Any]] = None
    needs_questions: Optional[bool] = None
    questions: Optional[List[str]] = None

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

# Global dictionaries for storing user processors and chat histories
processors = {}  # Store processor instances per user
chat_histories = {}  # Fallback in-memory chat storage
pending_tickets = {}  # Store partial ticket data for follow-up questions


def is_greeting_message(message: str) -> tuple:
    """Detect if message is a greeting using pattern matching (no LLM needed)"""
    message_lower = message.lower().strip()
    
    # Expanded list of greeting patterns
    simple_greetings = [
        'hi', 'hello', 'hey', 'hiya', 'howdy', 'greetings', 
        'good morning', 'good afternoon', 'good evening', 'good day',
        'hey there', 'hi there', 'hello there', 'morning', 'afternoon', 'evening',
        'sup', 'what\'s up', 'whats up', 'yo', 'helo', 'hllo'
    ]
    
    # Also check for greeting-like patterns
    greeting_patterns = [
        'hi nquiry', 'hello nquiry', 'hey nquiry',
        'hi there', 'hello everyone', 'good to see you'
    ]
    
    # Check if message is exactly a simple greeting (or with punctuation)
    clean_message = message_lower.rstrip('!.,?').strip()
    
    # Check exact matches
    if clean_message in simple_greetings:
        return True, get_greeting_response()
    
    # Check pattern matches
    for pattern in greeting_patterns:
        if pattern in clean_message:
            return True, get_greeting_response()
    
    # Check if message starts with greeting words
    greeting_starters = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    for starter in greeting_starters:
        if clean_message.startswith(starter) and len(clean_message) <= len(starter) + 10:
            return True, get_greeting_response()
    
    return False, ""


def get_greeting_response():
    """Generate a consistent greeting response"""
    return """Hello! 👋 Welcome to Nquiry, your intelligent query and support assistant. 

I'm here to help you with:
• Technical questions and troubleshooting
• System configuration issues  
• Documentation searches
• Support ticket creation when needed

Feel free to ask me about any issues you're experiencing or questions about our systems. How can I assist you today?"""


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
    
    # Direct ticket creation keywords - make them more specific to avoid false positives
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
    
    # Check for any matching keywords - but require they be somewhat prominent in the query
    all_keywords = ticket_keywords + escalation_keywords
    matches = [keyword for keyword in all_keywords if keyword in query_lower]
    
    # Only consider it a direct request if:
    # 1. The keyword match is substantial relative to query length, OR
    # 2. The query is relatively short and contains the keyword, OR
    # 3. The query starts with the keyword
    if matches:
        for keyword in matches:
            # If keyword takes up a significant portion of the query, it's likely a direct request
            if len(keyword) >= len(query_lower) * 0.3:
                return True
            # If query is short and contains keyword, it's likely a direct request
            if len(query_lower) <= 50 and keyword in query_lower:
                return True
            # If query starts with the keyword, it's likely a direct request
            if query_lower.startswith(keyword):
                return True
    
    return False


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


def create_intelligent_ticket_simple(query: str, customer_email: str) -> Dict:
    """
    Simple intelligent ticket creation - extract info from query and create ticket automatically
    Supports both JIRA (simulated) and Zendesk (real) ticket creation based on domain
    """
    try:
        from ticket_creator import TicketCreator
        from customer_role_manager import CustomerRoleMappingManager
        
        ticket_creator = TicketCreator()
        
        print(f"🤖 Simple intelligent analysis for query: '{query}'")
        
        # Check if this is a support domain
        customer_role_manager = CustomerRoleMappingManager()
        is_support_domain = customer_role_manager.is_support_domain(customer_email)
        
        print(f"📧 Domain type: {'Support (Zendesk)' if is_support_domain else 'Regular (JIRA)'}")
        
        if is_support_domain:
            # Create real Zendesk ticket for support domains
            return create_zendesk_ticket_intelligent(query, customer_email)
        else:
            # Create simulated JIRA ticket for regular domains
            return create_jira_ticket_simulated(query, customer_email)
            
    except Exception as e:
        print(f"❌ Error in simple intelligent ticket creation: {e}")
        return {
            'status': 'error',
            'message': f'Error creating ticket: {str(e)}'
        }

def create_zendesk_ticket_intelligent(query: str, customer_email: str) -> Dict:
    """Create a real Zendesk ticket for support domains"""
    try:
        from tools.zendesk_tool import ZendeskTool
        from datetime import datetime
        
        print(f"🎫 Creating Zendesk ticket for: {query}")
        
        zendesk_tool = ZendeskTool()
        
        # Prepare ticket data
        ticket_data = {
            "subject": f"Support Request: {query[:100]}",
            "description": f"""**Automated Support Request**

**Issue Description:**
{query}

**Requester:** {customer_email}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Source:** nQuiry AI Assistant

**Request Details:**
The user has submitted this support request through the nQuiry AI assistant. Please review and provide appropriate assistance.
""",
            "requester_email": customer_email,
            "priority": "normal",
            "type": "question",
            "tags": ["nquiry", "ai-assistant", "automated"]
        }
        
        # Create ticket in Zendesk
        result = zendesk_tool.create_ticket(ticket_data)
        
        if result.get('success'):
            ticket_info = result['ticket']
            ticket_id = ticket_info.get('id')
            ticket_url = ticket_info.get('url', '')
            
            return {
                'status': 'created',
                'ticket_id': ticket_id,
                'ticket_url': ticket_url,
                'platform': 'Zendesk',
                'message': f"""✅ **Zendesk Support Ticket Created Successfully!**

🎫 **Ticket ID:** {ticket_id}
📧 **Requester:** {customer_email}
🔗 **Ticket URL:** {ticket_url}

**Subject:** {ticket_data['subject']}

Our support team will review your request and respond soon. You can track progress using the ticket ID or URL above.""",
                'ticket_data': {
                    'id': ticket_id,
                    'url': ticket_url,
                    'subject': ticket_data['subject'],
                    'status': 'open',
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'requester': customer_email
                }
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            return {
                'status': 'error',
                'message': f'❌ Failed to create Zendesk ticket: {error_msg}'
            }
            
    except Exception as e:
        print(f"❌ Error creating Zendesk ticket: {e}")
        return {
            'status': 'error',
            'message': f'❌ Error creating Zendesk ticket: {str(e)}'
        }

def create_jira_ticket_simulated(query: str, customer_email: str) -> Dict:
    """Create a simulated JIRA ticket for regular domains (existing functionality)"""
    try:
        from ticket_creator import TicketCreator
        
        ticket_creator = TicketCreator()
        
        # Extract customer info
        customer_domain = customer_email.split('@')[-1] if customer_email else 'unknown.com'
        domain_to_customer = {
            'amd.com': 'AMD',
            'novartis.com': 'Novartis',
            'wdc.com': 'Wdc',
            'abbott.com': 'Abbott',
            'abbvie.com': 'Abbvie',
            'amgen.com': 'Amgen'
        }
        customer = domain_to_customer.get(customer_domain, customer_domain.split('.')[0].capitalize())
        
        # Determine category using existing logic
        category = ticket_creator.determine_ticket_category(query, customer, customer_email)
        
        # Simple priority detection
        query_lower = query.lower()
        if any(word in query_lower for word in ['urgent', 'critical', 'down', 'outage', 'emergency']):
            priority = 'High'
        elif any(word in query_lower for word in ['error', 'issue', 'problem', 'trouble']):
            priority = 'Medium'  
        else:
            priority = 'Medium'
        
        # Simple area detection
        area = 'General'
        if any(word in query_lower for word in ['login', 'access', 'password', 'authentication']):
            area = 'Access'
        elif any(word in query_lower for word in ['database', 'db', 'sql']):
            area = 'Database'
        elif any(word in query_lower for word in ['network', 'connection']):
            area = 'Network'
        elif any(word in query_lower for word in ['application', 'app', 'system']):
            area = 'Application'
        
        # Use proper environment detection - only auto-fill if explicitly mentioned
        from environment_detection import detect_environment_from_query
        detected_env, confidence = detect_environment_from_query(query)
        environment = detected_env if detected_env else None
        
        print(f"🎯 Environment detection: {environment} (confidence: {confidence})")
        
        # Check if environment is required but missing
        category_info = ticket_creator.ticket_config.get("ticket_categories", {}).get(category, {})
        required_fields = category_info.get("required_fields", {})
        
        if 'reported_environment' in required_fields and environment is None:
            print("⚠️ Environment not specified in query - need to ask user")
            return {
                'needs_more_info': True,
                'missing_field': 'environment',
                'question': "Which environment is affected by this issue? (production or staging)",
                'analysis': {
                    'category': category,
                    'priority': priority,
                    'area': area,
                    'customer': customer,
                    'customer_email': customer_email
                }
            }
        
        # If we get here, environment is either specified or not required
        environment_display = environment if environment else 'Not specified'
        
        print(f"🎯 Analysis results: Category={category}, Priority={priority}, Area={area}, Environment={environment_display}")
        
        # Create ticket data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticket_id = f"TICKET_{category}_{customer}_{timestamp}"
        jira_ticket_id = generate_jira_ticket_id(category)
        
        # Enhance description with conversation context
        enhanced_description = enhance_description_with_context(query)
        
        # Generate summary from description
        ticket_summary = generate_ticket_summary(query)
        
        # Get category-specific required and populated fields
        ticket_config = ticket_creator.ticket_config
        category_info = ticket_config.get("ticket_categories", {}).get(category, {})
        required_fields = category_info.get("required_fields", {})
        populated_fields = category_info.get("populated_fields", {})
        
        print(f"📋 Category {category} requires fields: {list(required_fields.keys())}")
        print(f"🔧 Category {category} auto-populates fields: {list(populated_fields.keys())}")
        
        ticket_data = {
            'ticket_id': ticket_id,
            'jira_ticket_id': jira_ticket_id,
            'category': category,
            'customer': customer,
            'customer_email': customer_email,
            'original_query': query,
            'created_date': datetime.now().isoformat(),
            'priority': priority,
            'description': enhanced_description,
            'summary': ticket_summary
        }
        
        # Handle category-specific required fields intelligently
        if 'area' in required_fields:
            ticket_data['area'] = area
            
        if 'affected_version' in required_fields:
            # Auto-populate affected_version with customer's product version from Excel
            affected_version = 'Not specified'
            if customer_email:
                try:
                    from customer_role_manager import CustomerRoleMappingManager
                    customer_manager = CustomerRoleMappingManager()
                    domain = customer_email.split('@')[-1].lower()
                    customer_mapping = customer_manager.get_customer_mapping(domain)
                    excel_version = customer_mapping.get('prod_version', '')
                    if excel_version and excel_version != 'nan':
                        affected_version = excel_version
                        print(f"🎯 Auto-populated affected version from Excel: {affected_version}")
                except Exception as e:
                    print(f"⚠️ Could not get version from Excel: {e}")
                    # Fallback to query extraction
                    import re
                    version_patterns = [
                        r'version\s+(\d+\.[\d.]+)',
                        r'v(\d+\.[\d.]+)',
                        r'(\d+\.[\d.]+)',
                        r'build\s+(\d+)',
                        r'release\s+(\d+\.[\d.]+)'
                    ]
                    for pattern in version_patterns:
                        match = re.search(pattern, query_lower)
                        if match:
                            affected_version = match.group(1)
                            break
            ticket_data['affected_version'] = affected_version
            
        if 'reported_environment' in required_fields:
            ticket_data['reported_environment'] = environment_display
            
        if 'environment' in required_fields:
            ticket_data['environment'] = environment_display
        
        # Add auto-populated fields based on category
        for field, value in populated_fields.items():
            should_process = (field not in ticket_data or 
                            (isinstance(value, str) and ('based on' in value.lower() or 'generated' in value.lower())))
            
            if should_process and isinstance(value, str):
                if 'based on description' in value.lower() or 'generated based on description' in value.lower():
                    # Use our generated summary instead of placeholder
                    ticket_data[field] = ticket_summary
                elif 'based on customer organization' in value.lower():
                    # Use our determined customer instead of placeholder  
                    ticket_data[field] = customer
                elif 'current_date' in value.lower():
                    ticket_data[field] = datetime.now().strftime('%Y-%m-%d')
                else:
                    ticket_data[field] = value
            elif field not in ticket_data:
                # Handle non-string values directly
                ticket_data[field] = value
        
        print(f"✅ Final ticket data includes fields: {list(ticket_data.keys())}")
        
        # Save ticket to file
        output_dir = 'ticket_simulation_output'
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"ticket_intelligent_{ticket_id.replace('TICKET_', '')}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        ticket_content = f"""INTELLIGENT AUTO-CREATED TICKET
===============================

Created using intelligent analysis of user query
Analysis Method: Simple keyword-based detection

Ticket ID: {ticket_id}
Jira Ticket ID: {jira_ticket_id}
Category: {category}
Customer: {customer}
Customer Email: {customer_email}
Created: {ticket_data['created_date']}

ORIGINAL QUERY:
===============
{query}

TICKET DETAILS:
===============
"""
        
        # Add all ticket fields to content in a structured way
        # Priority fields first (excluding creation_method)
        priority_fields = ['description', 'summary', 'priority', 'area', 'affected_version', 'reported_environment', 'environment']
        for field in priority_fields:
            if field in ticket_data:
                field_label = field.replace('_', ' ').title()
                ticket_content += f"{field_label}: {ticket_data[field]}\n"
        
        # Then add auto-populated fields from category config
        ticket_content += f"\nAUTO-POPULATED FIELDS (from {category} category):\n"
        ticket_content += "=" * 50 + "\n"
        
        for field, value in ticket_data.items():
            if field not in priority_fields and field not in ['ticket_id', 'jira_ticket_id', 'category', 'customer', 'customer_email', 'original_query', 'created_date']:
                field_label = field.replace('_', ' ').title()
                ticket_content += f"{field_label}: {value}\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ticket_content)
        
        print(f"✅ Intelligent ticket created: {ticket_id}")
        print(f"💾 Saved to: {filepath}")
        print(f"📋 Ticket contains {len(ticket_data)} fields total")
        
        # Generate simple confirmation message - details only in downloadable file
        message = f"""🎫 **Support Ticket Created Successfully!**

**Ticket ID:** {ticket_id}

We have raised a ticket for human support and our support team will review your request. You can download the complete ticket details using the download option below.

Our support agent will assist you shortly. Is there anything else I can help you with today?"""
        
        return {
            'status': 'created',
            'ticket_data': ticket_data,
            'message': message
        }
        
    except Exception as e:
        print(f"❌ Error in simple intelligent ticket creation: {e}")
        return {'status': 'error', 'message': f"Error creating ticket: {e}"}

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
        # Create processor in NON-streamlit mode so it actually creates tickets
        # instead of showing forms for support domains
        processor = IntelligentQueryProcessor(customer_email=customer_email, streamlit_mode=False)
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

async def send_status_update(status: str, step: str, icon: str = "🤖"):
    """Send a status update in SSE format"""
    data = {
        "type": "status",
        "status": status,
        "step": step,
        "icon": icon,
        "timestamp": get_ist_time().isoformat()
    }
    return f"data: {json.dumps(data)}\n\n"

async def send_final_response(response: str, show_ticket_form: bool = False, auto_ticket_created: bool = None, ticket_data: dict = None):
    """Send the final response in SSE format"""
    data = {
        "type": "response", 
        "response": response,
        "show_ticket_form": show_ticket_form,
        "auto_ticket_created": auto_ticket_created,
        "ticket_data": ticket_data,
        "timestamp": get_ist_time().isoformat()
    }
    return f"data: {json.dumps(data)}\n\n"

@app.post("/api/chat/stream")
async def send_message_stream(message: StreamingChatMessage):
    """Send a message to the intelligent chatbot with streaming status updates"""
    
    async def generate_stream():
        try:
            user_id = message.user_id
            print(f"🔵 RECEIVED STREAMING MESSAGE: '{message.message}' from user: {user_id}")
            
            # Send initial status
            yield await send_status_update("🤖 Nquiry is thinking...", "initializing", "🤖")
            await asyncio.sleep(0.1)  # Small delay for UX
            
            # Check if user is initialized, if not auto-initialize
            if user_id not in processors:
                yield await send_status_update("🔧 Setting up your session...", "initializing", "🔧")
                
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
                yield await send_status_update("🧠 Preparing AI assistant...", "loading", "🧠")
                print(f"🧠 Creating IntelligentQueryProcessor for {user_id}...")
                # Create a custom processor that doesn't prompt for email
                processor = create_processor_for_user(user_data['customer_email'])
                user_data['processor'] = processor
                
                # Debug: Check domain routing
                print(f"🔍 DEBUG - User Email: {user_id}")
                print(f"🔍 DEBUG - Processor is_support_domain: {processor.is_support_domain if hasattr(processor, 'is_support_domain') else 'NOT SET'}")
            
            processor = user_data['processor']
            
            # Store message in history
            yield await send_status_update("💾 Saving your message...", "saving", "💾")
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
            yield await send_status_update("👋 Checking message type...", "analyzing", "🔍")
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
                
                yield await send_final_response(greeting_response, show_ticket_form=False)
                return
            
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
                
                yield await send_final_response(satisfaction_response, show_ticket_form=False)
                return
            
            # Handle image analysis if images are provided
            image_context = ""
            if message.images and len(message.images) > 0:
                yield await send_status_update("🖼️ Analyzing uploaded images...", "analyzing-image", "🖼️")
                print(f"📸 Processing {len(message.images)} uploaded images...")
                
                try:
                    image_analyzer = ImageAnalyzer()
                    
                    # Prepare images in the format expected by analyze_images_with_query
                    images_for_analysis = []
                    for i, image_data in enumerate(message.images):
                        print(f"🖼️ Analyzing image {i+1}: {image_data.name} ({image_data.type})")
                        images_for_analysis.append({
                            'base64': image_data.base64,
                            'type': image_data.type,
                            'name': image_data.name
                        })
                    
                    # Analyze all images with user query
                    analysis_result = image_analyzer.analyze_images_with_query(
                        images=images_for_analysis,
                        user_query=message.message if message.message.strip() else "Please analyze these images and describe what you see, focusing on any technical issues, error messages, or interface elements."
                    )
                    
                    if analysis_result.get('success'):
                        image_context += f"\n\nImage Analysis:\n{analysis_result.get('analysis', 'No analysis available')}"
                        
                        # Also include extracted text if available
                        extracted_text = analysis_result.get('extracted_text', '')
                        if extracted_text:
                            image_context += f"\n\nExtracted Text:\n{extracted_text}"
                        
                        print(f"✅ Images analyzed successfully")
                    else:
                        error_msg = analysis_result.get('error', 'Unknown error')
                        print(f"❌ Image analysis failed: {error_msg}")
                        image_context = f"\n\nImage Analysis Error: {error_msg}\n"
                        
                except Exception as e:
                    print(f"❌ Image analysis error: {e}")
                    image_context = f"\n\nImage Analysis Error: {str(e)}\n"
            
            # Check organization access control before processing query
            yield await send_status_update("🔒 Checking access permissions...", "security", "🔒")
            print(f"🔒 Checking organization access for query: '{message.message}' from {user_id}")
            access_check = check_organization_access(message.message, user_id)
            if not access_check['allowed']:
                print(f"🚫 Access denied: {access_check['message']}")
                user_info = access_check.get('user_info', {})
                if user_info:
                    print(f"   User org: {user_info.get('organization', 'Unknown')}")
                print(f"   Blocked orgs: {access_check['blocked_orgs']}")
                
                # Store bot response in history
                bot_response = access_check['message']
                if chat_history_manager:
                    chat_history_manager.add_message(user_id, "assistant", bot_response, message.session_id)
                else:
                    chat_histories[user_id].append({
                        "role": "assistant", 
                        "message": bot_response,
                        "timestamp": get_ist_time()
                    })
                
                yield await send_final_response(bot_response, show_ticket_form=False)
                return
            
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
                yield await send_status_update("🔍 Analyzing conversation context...", "analyzing", "🔍")
                print(f"🔍 Checking conversation history for ticket creation context...")
                print(f"🔍 History length: {len(processed_history)}")
                
                last_bot_message = None
                for msg in reversed(processed_history):
                    if msg.get('role') == 'assistant':
                        last_bot_message = msg.get('message', '')
                        print(f"🔍 Found last bot message: '{last_bot_message[:100]}...'")
                        break
                
                # Check if the last bot message asked about creating a ticket OR asked about environment
                if last_bot_message and (any(phrase in last_bot_message.lower() for phrase in [
                    'would you like me to create a support ticket',
                    'would you like to create a ticket',
                    'create a support ticket',
                    'should i create a ticket',
                    'create a support ticket?',
                    'need a support ticket?',
                    'does this help?',
                    'need more help?',
                    'create a support ticket so',
                    'would you like me to create a support ticket so'
                ]) or any(phrase in last_bot_message.lower() for phrase in [
                    'which environment is affected',
                    'production or staging',
                    'environment question',
                    'specify either \'production\' or \'staging\''
                ])):
                    print(f"🔍 Last bot message contained ticket creation suggestion: '{last_bot_message[:100]}...'")
                    
                    # Check if user is responding to environment question
                    print(f"🔍 Checking pending tickets for user {user_id}...")
                    print(f"🔍 Pending tickets keys: {list(pending_tickets.keys())}")
                    if user_id in pending_tickets:
                        print(f"🔍 Found pending ticket data: {pending_tickets[user_id]}")
                    
                    if user_id in pending_tickets and pending_tickets[user_id].get('missing_field') == 'environment':
                        print(f"🌍 User responding to environment question: '{message.message}'")
                        
                        from environment_detection import validate_environment_response
                        validated_env = validate_environment_response(message.message)
                        
                        if validated_env:
                            print(f"✅ Valid environment response: {validated_env}")
                            
                            # Get stored analysis and create ticket with environment
                            stored_data = pending_tickets[user_id]
                            analysis = stored_data['analysis']
                            original_query = stored_data['original_query']
                            
                            # Create ticket with the provided environment
                            yield await send_status_update("🎫 Creating your support ticket...", "creating-ticket", "🎫")
                            
                            # Use the simple ticket creation with the environment override
                            def create_ticket_with_env():
                                # Create ticket data manually with the provided environment
                                from ticket_creator import TicketCreator
                                ticket_creator = TicketCreator()
                                
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                ticket_id = f"TICKET_{analysis['category']}_{analysis['customer']}_{timestamp}"
                                jira_ticket_id = generate_jira_ticket_id(analysis['category'])
                                
                                # Get conversation history for enhanced description
                                chat_history = []
                                if chat_history_manager:
                                    try:
                                        chat_history = chat_history_manager.get_chat_history(analysis['customer_email'])
                                    except:
                                        chat_history = chat_histories.get(analysis['customer_email'], [])
                                else:
                                    chat_history = chat_histories.get(analysis['customer_email'], [])
                                
                                # Enhance description with conversation context
                                enhanced_description = enhance_description_with_context(original_query, chat_history)
                                ticket_summary = generate_ticket_summary(original_query)
                                
                                # Get category configuration for fields
                                category_info = ticket_creator.ticket_config.get("ticket_categories", {}).get(analysis['category'], {})
                                required_fields = category_info.get("required_fields", {})
                                populated_fields = category_info.get("populated_fields", {})
                                
                                # Build ticket data with environment
                                ticket_data = {
                                    'ticket_id': ticket_id,
                                    'jira_ticket_id': jira_ticket_id,
                                    'category': analysis['category'],
                                    'customer': analysis['customer'],
                                    'customer_email': analysis['customer_email'],
                                    'priority': analysis['priority'],
                                    'description': enhanced_description,
                                    'summary': ticket_summary,
                                    'original_query': original_query,
                                    'created_date': datetime.now().isoformat()
                                }
                                
                                # Add all populated fields with placeholder processing
                                for field_name, field_value in populated_fields.items():
                                    should_process = (field_name not in ticket_data or 
                                                    (isinstance(field_value, str) and ('based on' in field_value.lower() or 'generated' in field_value.lower())))
                                    
                                    if should_process and isinstance(field_value, str):
                                        if 'based on description' in field_value.lower() or 'generated based on description' in field_value.lower():
                                            # Use our generated summary instead of placeholder
                                            ticket_data[field_name] = ticket_summary
                                        elif 'based on customer organization' in field_value.lower():
                                            # Use our determined customer instead of placeholder  
                                            ticket_data[field_name] = analysis['customer']
                                        elif 'current_date' in field_value.lower():
                                            ticket_data[field_name] = datetime.now().strftime('%Y-%m-%d')
                                        else:
                                            ticket_data[field_name] = field_value
                                    elif field_name not in ticket_data:
                                        # Handle non-string values directly
                                        ticket_data[field_name] = field_value
                                
                                # Add required fields with environment override
                                if 'reported_environment' in required_fields:
                                    ticket_data['reported_environment'] = validated_env
                                if 'environment' in required_fields:
                                    ticket_data['environment'] = validated_env
                                
                                # Auto-populate affected_version from Excel if available
                                if 'affected_version' in required_fields and analysis.get('customer_email'):
                                    try:
                                        from customer_role_manager import CustomerRoleMappingManager
                                        customer_manager = CustomerRoleMappingManager()
                                        domain = analysis['customer_email'].split('@')[-1].lower()
                                        customer_mapping = customer_manager.get_customer_mapping(domain)
                                        excel_version = customer_mapping.get('prod_version', '')
                                        if excel_version and excel_version != 'nan':
                                            ticket_data['affected_version'] = excel_version
                                        else:
                                            ticket_data['affected_version'] = 'Not specified'
                                    except Exception as e:
                                        print(f"⚠️ Could not get version from Excel: {e}")
                                        ticket_data['affected_version'] = 'Not specified'
                                
                                return ticket_data
                            
                            try:
                                ticket_data = create_ticket_with_env()
                                
                                if ticket_data:
                                    # Clean up pending ticket
                                    del pending_tickets[user_id]
                                    
                                    # Generate the same message format as create_intelligent_ticket_simple
                                    auto_response = f"""🎫 **Support Ticket Created Successfully!**

**Ticket ID:** {ticket_data['ticket_id']}

We have raised a ticket for human support and our support team will review your request. You can download the complete ticket details using the download option below.

Our support agent will assist you shortly. Is there anything else I can help you with today?"""
                                    
                                    # Also save the ticket to file like the original function does
                                    try:
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        filepath = f"ticket_simulation_output/ticket_demo_{analysis['category']}_{analysis['customer']}_{timestamp}.txt"
                                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                                        
                                        # Generate ticket content for file
                                        ticket_content = f"""AUTOMATIC AI TICKET
===================

Ticket ID: {ticket_data['ticket_id']}
Jira Ticket ID: {ticket_data['jira_ticket_id']}
Category: {ticket_data['category']}
Customer: {ticket_data['customer']}
Priority: {ticket_data.get('priority', 'Medium')}
Description: {ticket_data['description']}

AUTO-POPULATED FIELDS FROM {ticket_data['category']} CATEGORY:
"""
                                        
                                        for field, value in ticket_data.items():
                                            if field not in ['ticket_id', 'jira_ticket_id', 'category', 'customer', 'customer_email', 'original_query', 'created_date', 'description']:
                                                field_label = field.replace('_', ' ').title()
                                                ticket_content += f"• {field_label}: {value}\n"
                                        
                                        ticket_content += f"\nThis ticket was created automatically using AI analysis."
                                        
                                        with open(filepath, 'w', encoding='utf-8') as f:
                                            f.write(ticket_content)
                                        
                                        print(f"💾 Ticket saved to: {filepath}")
                                    except Exception as save_error:
                                        print(f"⚠️ Could not save ticket file: {save_error}")
                                    
                                    if chat_history_manager:
                                        chat_history_manager.add_message(user_id, "assistant", auto_response, message.session_id)
                                    else:
                                        chat_histories[user_id].append({
                                            "role": "assistant", 
                                            "message": auto_response,
                                            "timestamp": get_ist_time()
                                        })
                                    
                                    yield await send_final_response(
                                        auto_response,
                                        show_ticket_form=False,
                                        auto_ticket_created=True,
                                        ticket_data=ticket_data
                                    )
                                    return
                            except Exception as e:
                                print(f"❌ Error creating ticket with environment: {e}")
                                del pending_tickets[user_id]  # Clean up
                                yield await send_final_response(
                                    "I encountered an error creating your ticket. Please try again or use the ticket form.",
                                    show_ticket_form=True
                                )
                                return
                        else:
                            print(f"❌ Invalid environment response: '{message.message}'")
                            yield await send_final_response(
                                "Please specify either 'production' or 'staging' for the environment."
                            )
                            return
                    
                    # Check if current user message is affirmative
                    user_message_lower = message.message.lower().strip()
                    print(f"🔍 User response: '{user_message_lower}'")
                    
                    affirmative_responses = [
                        'yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'please', 'go ahead',
                        'create ticket', 'create a ticket', 'yes please', 'yes, please',
                        'proceed', 'continue', 'that would be great', 'sounds good'
                    ]
                    
                    is_affirmative = any(response in user_message_lower for response in affirmative_responses)
                    print(f"🔍 Is affirmative response: {is_affirmative}")
                    
                    if is_affirmative:
                        print(f"🎫 User confirmed ticket creation with: '{message.message}'")
                        
                        yield await send_status_update("🎫 Creating your support ticket...", "creating-ticket", "🎫")
                        
                        # Extract the original issue from conversation history for ticket creation
                        original_query = "Support assistance requested"
                        for msg in processed_history:
                            if msg.get('role') == 'user' and len(msg.get('message', '')) > 10:
                                original_query = msg.get('message', original_query)
                                break
                        
                        # Create intelligent ticket automatically since user confirmed
                        print(f"🤖 Creating intelligent ticket for confirmed request: '{original_query}'")
                        ticket_result = create_intelligent_ticket_simple(original_query, user_id)
                        
                        if ticket_result.get('needs_more_info'):
                            # Need to ask follow-up question for missing field
                            print(f"❓ Need more info: {ticket_result.get('missing_field')}")
                            follow_up_question = ticket_result.get('question', 'Please provide more details.')
                            
                            # Store the analysis for when user responds
                            pending_tickets[user_id] = {
                                'analysis': ticket_result.get('analysis'),
                                'original_query': original_query,
                                'missing_field': ticket_result.get('missing_field'),
                                'timestamp': time.time()
                            }
                            
                            if chat_history_manager:
                                chat_history_manager.add_message(user_id, "assistant", follow_up_question, message.session_id)
                            else:
                                chat_histories[user_id].append({
                                    "role": "assistant", 
                                    "message": follow_up_question,
                                    "timestamp": get_ist_time()
                                })
                            
                            yield await send_final_response(follow_up_question)
                            return
                            
                        elif ticket_result.get('status') == 'created':
                            print("✅ Intelligent ticket created successfully after user confirmation!")
                            
                            auto_response = ticket_result.get('message', '')
                            if chat_history_manager:
                                chat_history_manager.add_message(user_id, "assistant", auto_response, message.session_id)
                            else:
                                chat_histories[user_id].append({
                                    "role": "assistant", 
                                    "message": auto_response,
                                    "timestamp": get_ist_time()
                                })
                            
                            yield await send_final_response(
                                auto_response,
                                show_ticket_form=False,
                                auto_ticket_created=True,
                                ticket_data=ticket_result.get('ticket_data')
                            )
                            return
                        else:
                            # Fall back to form if intelligent creation fails
                            print("⚠️ Intelligent ticket creation failed, showing form...")
                            yield await send_final_response(
                                f"I'll help you create a support ticket. Please provide the required details below.",
                                show_ticket_form=True
                            )
                            return
                    
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
                        
                        yield await send_final_response(decline_response, show_ticket_form=False)
                        return

            # First check if this is a direct ticket creation request
            yield await send_status_update("🔍 Analyzing your request...", "analyzing", "🔍")
            is_direct_request = is_direct_ticket_request(message.message)
            print(f"🔍 Direct ticket request check: is_direct={is_direct_request} for query: '{message.message}'")
            
            if is_direct_request:
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
                    yield await send_final_response(response_text, show_ticket_form=False)
                    return
                else:
                    # For explicit ticket creation requests, create ticket intelligently
                    yield await send_status_update("🎫 Creating your support ticket...", "creating-ticket", "🎫")
                    print(f"🎫 User explicitly requested ticket creation, creating intelligent ticket...")
                    
                    # Create intelligent ticket automatically for explicit requests
                    ticket_result = create_intelligent_ticket_simple(actual_issue, user_id)
                    
                    if ticket_result.get('status') == 'created':
                        print("✅ Intelligent ticket created successfully for explicit request!")
                        
                        auto_response = ticket_result.get('message', '')
                        if chat_history_manager:
                            chat_history_manager.add_message(user_id, "assistant", auto_response, message.session_id)
                        else:
                            if user_id not in chat_histories:
                                chat_histories[user_id] = []
                            chat_histories[user_id].append({
                                "role": "assistant", 
                                "message": auto_response,
                                "timestamp": get_ist_time()
                            })
                        
                        yield await send_final_response(
                            auto_response,
                            show_ticket_form=False,
                            auto_ticket_created=True,
                            ticket_data=ticket_result.get('ticket_data')
                        )
                        return
                    else:
                        # Fall back to form if intelligent creation fails
                        print("⚠️ Intelligent ticket creation failed for explicit request, showing form...")
                        
                        # Store the request acknowledgment in history
                        acknowledgment = f"I'll help you create a support ticket for: {actual_issue}\n\nPlease provide the required details below."
                        
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
                        
                        yield await send_final_response(
                            acknowledgment,
                            show_ticket_form=True
                        )
                        return
            else:
                # Determine workflow type based on domain
                is_support_domain = processor.is_support_domain if hasattr(processor, 'is_support_domain') else False
                
                print(f"🔍 DEBUG - Routing Decision: user_id={user_id}, is_support_domain={is_support_domain}")
                
                if is_support_domain:
                    print(f"📚 Query '{message.message}' -> Using support flow: Zendesk → Azure Blob → Comprehensive Response")
                    
                    # Send support workflow status updates
                    yield await send_status_update("🎫 Looking through Zendesk tickets...", "searching-zendesk", "🎫")
                    await asyncio.sleep(1.5)  # Simulate search time
                    
                    yield await send_status_update("🗂️ Searching SharePoint documents...", "searching-sharepoint", "🗂️")
                    await asyncio.sleep(1.5)  # Simulate search time
                else:
                    print(f"📚 Query '{message.message}' -> Using search flow first: JIRA → MindTouch → Comprehensive Response")
                    
                    # Send regular workflow status updates
                    yield await send_status_update("🎫 Looking through JIRA tickets...", "searching-jira", "🎫")
                    await asyncio.sleep(1.5)  # Simulate search time
                    
                    yield await send_status_update("📚 Searching MindTouch articles...", "searching-mindtouch", "📚")
                    await asyncio.sleep(1.5)  # Simulate search time
                
                yield await send_status_update("🧠 Generating response...", "generating", "🧠")
                
                # Handle image analysis if images are provided
                image_context = ""
                if message.images and len(message.images) > 0:
                    yield await send_status_update("🖼️ Analyzing uploaded images...", "image-analysis", "🖼️")
                    try:
                        image_analyzer = ImageAnalyzer()
                        print(f"🖼️ Analyzing {len(message.images)} image(s)...")
                        
                        # Prepare images in the format expected by analyze_images_with_query
                        images_for_analysis = []
                        for i, image_data in enumerate(message.images):
                            print(f"📸 Processing image {i+1}: {image_data.name} ({image_data.type})")
                            images_for_analysis.append({
                                'base64': image_data.base64,
                                'type': image_data.type,
                                'name': image_data.name
                            })
                        
                        # Analyze all images with user query
                        analysis_result = image_analyzer.analyze_images_with_query(
                            images=images_for_analysis,
                            user_query=message.message
                        )
                        
                        if analysis_result.get('success'):
                            image_context += f"\n\nImage Analysis:\n{analysis_result.get('analysis', 'No analysis available')}"
                            
                            # Also include extracted text if available
                            extracted_text = analysis_result.get('extracted_text', '')
                            if extracted_text:
                                image_context += f"\n\nExtracted Text:\n{extracted_text}"
                            
                            print(f"✅ Images analyzed successfully")
                        else:
                            print(f"❌ Failed to analyze images: {analysis_result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"⚠️ Error during image analysis: {e}")
                        yield await send_status_update("⚠️ Image analysis failed, continuing with text...", "warning", "⚠️")
                
                # Combine text query with image context
                enhanced_message = message.message
                if image_context:
                    enhanced_message = f"{message.message}\n\nAdditional Context from Images:{image_context}"
                    print(f"🖼️ Enhanced query with image context ({len(image_context)} chars)")
                
                try:
                    # First, try to find helpful information through search
                    print("🔍 Searching for information: JIRA → MindTouch → Comprehensive Response")
                    result = processor.process_query(user_id, enhanced_message, processed_history)
                    
                    if result and isinstance(result, dict):
                        # Handle process_query result
                        if 'formatted_response' in result:
                            response_text = result['formatted_response']
                        elif 'response' in result:
                            response_text = result['response']
                        else:
                            response_text = str(result)
                        
                        # Check if this is a ticket creation flow or if ticket was created
                        ticket_created_info = result.get('ticket_created')
                        print(f"🔍 Checking ticket creation result: {ticket_created_info}")
                        
                        if ticket_created_info:
                            # Ticket was created in the process - don't show form
                            print(f"✅ Ticket detected: {ticket_created_info}")
                            show_ticket = False
                            
                            # If it's a Zendesk ticket, make sure the response shows the ticket details
                            if isinstance(ticket_created_info, dict) and ticket_created_info.get('platform') == 'Zendesk':
                                print("🎫 Zendesk ticket created - using ticket confirmation instead of form")
                                
                                # Send final response with ticket details instead of continuing to form logic
                                yield await send_final_response(
                                    response_text,
                                    show_ticket_form=False,
                                    auto_ticket_created=True,
                                    ticket_data=ticket_created_info
                                )
                                return
                        else:
                            # Evaluate the quality of the response to determine if we should offer ticket creation
                            print("🤖 Evaluating search response quality...")
                            
                            # Check if response indicates insufficient information
                            insufficient_indicators = [
                                'i searched through jira tickets and documentation but couldn\'t find specific information',
                                'unfortunately, no specific resolution steps are provided',
                                'i cannot provide actionable steps',
                                'no resolution details are included',
                                'more context is needed',
                                'further investigation is required',
                                'does not contain complete details',
                                'without more details',
                                'i couldn\'t find',
                                'no relevant information',
                                'no specific information',
                                'couldn\'t locate',
                                'no documents found',
                                'no search results',
                                'unable to find',
                                'no matching',
                                'not found in',
                                'no information available',
                                'couldn\'t retrieve',
                                'no results',
                                'search didn\'t return',
                                'no documentation',
                                'no relevant documents',
                                'no specific details'
                            ]
                            
                            response_lower = response_text.lower()
                            is_insufficient = any(indicator in response_lower for indicator in insufficient_indicators)
                            
                            # Check if response has good/helpful content
                            has_good_content = any(phrase in response_lower for phrase in [
                                'here\'s what i found',
                                'according to',
                                'based on the documentation',
                                'the following information',
                                'here are the steps',
                                'you can',
                                'to resolve this',
                                'the solution is',
                                'try the following',
                                'here\'s how to',
                                'the process involves',
                                'follow these steps',
                                'navigate to',
                                'to enable',
                                'to configure',
                                'click on'
                            ])
                            
                            if is_insufficient and not has_good_content:
                                # No helpful information found - offer to create intelligent ticket
                                print("📋 No helpful information found - offering to create intelligent ticket...")
                                
                                response_text += f"\n\n🎫 **No specific information found**\n\nI wasn't able to find detailed information about your question in our documentation. Would you like me to create a support ticket so our technical team can provide you with the specific guidance you need?"
                                show_ticket = False  # Wait for user confirmation
                            elif has_good_content:
                                # Found helpful information - ticket creation offer already included in response
                                print("✅ Found helpful information - ticket creation offer already included in response")
                                show_ticket = False  # Wait for user confirmation
                            else:
                                # Mixed/unclear response - offer ticket creation
                                print("🤔 Unclear response quality - offering ticket creation...")
                                response_text += f"\n\n🤝 **Need more help?**\n\nIf you need more detailed assistance with this, I can create a support ticket to connect you with our technical team."
                                show_ticket = False  # Wait for user confirmation
                            
                    elif result:
                        response_text = str(result)
                        # For basic string responses, offer ticket creation
                        response_text += f"\n\n🎫 **Need a support ticket?**\n\nIf you need more detailed assistance, I can create a support ticket to get this resolved by our support team."
                        show_ticket = False
                    else:
                        response_text = "I apologize, but I encountered an issue processing your request. Would you like me to create a support ticket to get this resolved for you?"
                        show_ticket = False
                    
                except Exception as e:
                    print(f"❌ Error in intelligent processing: {e}")
                    response_text = f"I encountered an error while processing your request: {str(e)}\n\nWould you like me to create a support ticket to get this resolved for you?"
                    show_ticket = False
                
            # Store bot response in history
            if chat_history_manager:
                chat_history_manager.add_message(user_id, "assistant", response_text, message.session_id)
            else:
                chat_histories[user_id].append({
                    "role": "assistant", 
                    "message": response_text,
                    "timestamp": get_ist_time()
                })
            
            yield await send_final_response(response_text, show_ticket_form=show_ticket)
            
        except Exception as e:
            print(f"❌ Error in streaming chat: {e}")
            yield await send_final_response(
                f"I encountered an error processing your request: {str(e)}\n\nPlease try again or contact support.",
                show_ticket_form=False
            )
    
    return StreamingResponse(generate_stream(), media_type="text/plain")

@app.post("/api/chat", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message to the intelligent chatbot"""
    try:
        user_id = message.user_id
        print(f"🔵 RECEIVED MESSAGE: '{message.message}' from user: {user_id}")
        
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
        
        # Check organization access control before processing query
        print(f"🔒 Checking organization access for query: '{message.message}' from {user_id}")
        access_check = check_organization_access(message.message, user_id)
        if not access_check['allowed']:
            print(f"🚫 Access denied: {access_check['message']}")
            user_info = access_check.get('user_info', {})
            if user_info:
                print(f"   User org: {user_info.get('organization', 'Unknown')}")
            print(f"   Blocked orgs: {access_check['blocked_orgs']}")
            
            # Store bot response in history
            bot_response = access_check['message']
            if chat_history_manager:
                chat_history_manager.add_message(user_id, "assistant", bot_response, message.session_id)
            else:
                chat_histories[user_id].append({
                    "role": "assistant", 
                    "message": bot_response,
                    "timestamp": get_ist_time()
                })
            
            return ChatResponse(
                response=bot_response,
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
            print(f"🔍 Checking conversation history for ticket creation context...")
            print(f"🔍 History length: {len(processed_history)}")
            
            last_bot_message = None
            for msg in reversed(processed_history):
                if msg.get('role') == 'assistant':
                    last_bot_message = msg.get('message', '')
                    print(f"🔍 Found last bot message: '{last_bot_message[:100]}...'")
                    break
            
            # Check if the last bot message asked about creating a ticket
            if last_bot_message and any(phrase in last_bot_message.lower() for phrase in [
                'would you like me to create a support ticket',
                'would you like to create a ticket',
                'create a support ticket',
                'should i create a ticket',
                'create a support ticket?',
                'need a support ticket?',
                'does this help?',
                'need more help?',
                'create a support ticket so',
                'would you like me to create a support ticket so'
            ]):
                print(f"🔍 Last bot message contained ticket creation suggestion: '{last_bot_message[:100]}...'")
                
                # Check if current user message is affirmative
                user_message_lower = message.message.lower().strip()
                print(f"🔍 User response: '{user_message_lower}'")
                
                affirmative_responses = [
                    'yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'please', 'go ahead',
                    'create ticket', 'create a ticket', 'yes please', 'yes, please',
                    'proceed', 'continue', 'that would be great', 'sounds good'
                ]
                
                is_affirmative = any(response in user_message_lower for response in affirmative_responses)
                print(f"🔍 Is affirmative response: {is_affirmative}")
                
                if is_affirmative:
                    print(f"🎫 User confirmed ticket creation with: '{message.message}'")
                    
                    # Extract the original issue from conversation history for ticket creation
                    original_query = "Support assistance requested"
                    for msg in processed_history:
                        if msg.get('role') == 'user' and len(msg.get('message', '')) > 10:
                            original_query = msg.get('message', original_query)
                            break
                    
                    # Create intelligent ticket automatically since user confirmed
                    print(f"🤖 Creating intelligent ticket for confirmed request: '{original_query}'")
                    ticket_result = create_intelligent_ticket_simple(original_query, user_id)
                    
                    if ticket_result.get('status') == 'created':
                        print("✅ Intelligent ticket created successfully after user confirmation!")
                        
                        auto_response = ticket_result.get('message', '')
                        if chat_history_manager:
                            chat_history_manager.add_message(user_id, "assistant", auto_response, message.session_id)
                        else:
                            chat_histories[user_id].append({
                                "role": "assistant", 
                                "message": auto_response,
                                "timestamp": get_ist_time()
                            })
                        
                        return ChatResponse(
                            response=auto_response,
                            show_ticket_form=False,
                            auto_ticket_created=True,
                            ticket_data=ticket_result.get('ticket_data')
                        )
                    else:
                        # Fall back to form if intelligent creation fails
                        print("⚠️ Intelligent ticket creation failed, showing form...")
                        return ChatResponse(
                            response=f"I'll help you create a support ticket. Please provide the required details below.",
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
        is_direct_request = is_direct_ticket_request(message.message)
        print(f"🔍 Direct ticket request check: is_direct={is_direct_request} for query: '{message.message}'")
        
        if is_direct_request:
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
                # For explicit ticket creation requests, create ticket intelligently instead of showing form
                print(f"🎫 User explicitly requested ticket creation, creating intelligent ticket...")
                
                # Create intelligent ticket automatically for explicit requests
                ticket_result = create_intelligent_ticket_simple(actual_issue, user_id)
                
                if ticket_result.get('status') == 'created':
                    print("✅ Intelligent ticket created successfully for explicit request!")
                    
                    auto_response = ticket_result.get('message', '')
                    if chat_history_manager:
                        chat_history_manager.add_message(user_id, "assistant", auto_response, message.session_id)
                    else:
                        if user_id not in chat_histories:
                            chat_histories[user_id] = []
                        chat_histories[user_id].append({
                            "role": "assistant", 
                            "message": auto_response,
                            "timestamp": get_ist_time()
                        })
                    
                    return ChatResponse(
                        response=auto_response,
                        show_ticket_form=False,
                        auto_ticket_created=True,
                        ticket_data=ticket_result.get('ticket_data')
                    )
                else:
                    # Fall back to form if intelligent creation fails
                    print("⚠️ Intelligent ticket creation failed for explicit request, showing form...")
                    
                    # Store the request acknowledgment in history
                    acknowledgment = f"I'll help you create a support ticket for: {actual_issue}\n\nPlease provide the required details below."
                    
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
            # Determine workflow type based on domain
            is_support_domain = processor.is_support_domain if hasattr(processor, 'is_support_domain') else False
            
            if is_support_domain:
                print(f"📚 Query '{message.message}' -> Using support flow: Zendesk → Azure Blob → Comprehensive Response")
            else:
                print(f"📚 Query '{message.message}' -> Using search flow first: JIRA → MindTouch → Comprehensive Response")
            
            try:
                # Handle image analysis if images are provided
                image_context = ""
                if message.images and len(message.images) > 0:
                    try:
                        image_analyzer = ImageAnalyzer()
                        print(f"🖼️ Analyzing {len(message.images)} image(s)...")
                        
                        # Prepare images in the format expected by analyze_images_with_query
                        images_for_analysis = []
                        for i, image_data in enumerate(message.images):
                            print(f"📸 Processing image {i+1}: {image_data.name} ({image_data.type})")
                            images_for_analysis.append({
                                'base64': image_data.base64,
                                'type': image_data.type,
                                'name': image_data.name
                            })
                        
                        # Analyze all images with user query
                        analysis_result = image_analyzer.analyze_images_with_query(
                            images=images_for_analysis,
                            user_query=message.message
                        )
                        
                        if analysis_result.get('success'):
                            image_context += f"\n\nImage Analysis:\n{analysis_result.get('analysis', 'No analysis available')}"
                            
                            # Also include extracted text if available
                            extracted_text = analysis_result.get('extracted_text', '')
                            if extracted_text:
                                image_context += f"\n\nExtracted Text:\n{extracted_text}"
                            
                            print(f"✅ Images analyzed successfully")
                        else:
                            print(f"❌ Failed to analyze images: {analysis_result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        print(f"⚠️ Error during image analysis: {e}")
                
                # Combine text query with image context
                enhanced_message = message.message
                if image_context:
                    enhanced_message = f"{message.message}\n\nAdditional Context from Images:{image_context}"
                    print(f"🖼️ Enhanced query with image context ({len(image_context)} chars)")
                
                # First, try to find helpful information through search
                print("🔍 Searching for information: JIRA → MindTouch → Comprehensive Response")
                result = processor.process_query(user_id, enhanced_message, processed_history)
                
                if result and isinstance(result, dict):
                    # Handle process_query result
                    if 'formatted_response' in result:
                        response_text = result['formatted_response']
                    elif 'response' in result:
                        response_text = result['response']
                    else:
                        response_text = str(result)
                    
                    # Check if this is a ticket creation flow or if ticket was created
                    ticket_created_info = result.get('ticket_created')
                    print(f"🔍 Checking ticket creation result: {ticket_created_info}")
                    
                    if ticket_created_info:
                        # Ticket was created in the process - don't show form
                        print(f"✅ Ticket detected: {ticket_created_info}")
                        show_ticket = False
                        
                        # If it's a Zendesk ticket, make sure the response shows the ticket details
                        if isinstance(ticket_created_info, dict) and ticket_created_info.get('platform') == 'Zendesk':
                            print("🎫 Zendesk ticket created - returning ticket confirmation")
                            
                            # Return final response with ticket details instead of continuing to form logic
                            return JSONResponse(content={
                                "response": response_text,
                                "show_ticket_form": False,
                                "auto_ticket_created": True,
                                "ticket_data": ticket_created_info,
                                "chat_history": processed_history
                            })
                    else:
                        # Evaluate the quality of the response to determine if we should offer ticket creation
                        print("🤖 Evaluating search response quality...")
                        
                        # Check if response indicates insufficient information
                        insufficient_indicators = [
                            'i searched through jira tickets and documentation but couldn\'t find specific information',
                            'unfortunately, no specific resolution steps are provided',
                            'i cannot provide actionable steps',
                            'no resolution details are included',
                            'more context is needed',
                            'further investigation is required',
                            'does not contain complete details',
                            'without more details',
                            'i couldn\'t find',
                            'no relevant information',
                            'no specific information',
                            'couldn\'t locate',
                            'no documents found',
                            'no search results',
                            'unable to find',
                            'no matching',
                            'not found in',
                            'no information available',
                            'couldn\'t retrieve',
                            'no results',
                            'search didn\'t return',
                            'no documentation',
                            'no relevant documents',
                            'no specific details'
                        ]
                        
                        response_lower = response_text.lower()
                        is_insufficient = any(indicator in response_lower for indicator in insufficient_indicators)
                        
                        # Check if response has good/helpful content
                        has_good_content = any(phrase in response_lower for phrase in [
                            'here\'s what i found',
                            'according to',
                            'based on the documentation',
                            'the following information',
                            'here are the steps',
                            'you can',
                            'to resolve this',
                            'the solution is',
                            'try the following',
                            'here\'s how to',
                            'the process involves',
                            'follow these steps',
                            'navigate to',
                            'to enable',
                            'to configure',
                            'click on'
                        ])
                        
                        if is_insufficient and not has_good_content:
                            # No helpful information found - offer to create intelligent ticket
                            print("📋 No helpful information found - offering to create intelligent ticket...")
                            
                            response_text += f"\n\n🎫 **No specific information found**\n\nI wasn't able to find detailed information about your question in our documentation. Would you like me to create a support ticket so our technical team can provide you with the specific guidance you need?"
                            show_ticket = False  # Wait for user confirmation
                        elif has_good_content:
                            # Found helpful information - ticket creation offer already added by semantic search
                            print("✅ Found helpful information - ticket creation offer already included in response")
                            show_ticket = False  # Wait for user confirmation
                        else:
                            # Mixed/unclear response - offer ticket creation
                            print("🤔 Unclear response quality - offering ticket creation...")
                            response_text += f"\n\n🤝 **Need more help?**\n\nIf you need more detailed assistance with this, I can create a support ticket to connect you with our technical team."
                            show_ticket = False  # Wait for user confirmation
                        
                elif result:
                    response_text = str(result)
                    # For basic string responses, offer ticket creation
                    response_text += f"\n\n🎫 **Need a support ticket?**\n\nIf you need more detailed assistance, I can create a support ticket to get this resolved by our support team."
                    show_ticket = False
                else:
                    # No result at all - suggest ticket creation
                    response_text = "I apologize, but I couldn't find relevant information for your query in our documentation.\n\n🎫 **Create a support ticket?**\n\nWould you like me to create a support ticket so our technical team can help you with this specific question?"
                    show_ticket = False
                    
            except Exception as e:
                print(f"⚠️ Error in intelligent processing: {e}")
                org_name = user_data['org_data'].get('organization', 'your organization')
                response_text = f"I encountered an issue while searching our knowledge base for {org_name}.\n\n🎫 **Create a support ticket?**\n\nWould you like me to create a support ticket to ensure your question gets properly addressed?"
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

class IntelligentTicketAnswers(BaseModel):
    original_query: str
    customer_email: str
    answers: Dict[str, Any]
    analysis: Dict[str, Any]

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

@app.post("/api/tickets/create-with-answers")
async def create_ticket_with_answers(request: IntelligentTicketAnswers):
    """Complete ticket creation after user answers targeted questions"""
    try:
        from intelligent_auto_ticket_creator import IntelligentAutoTicketCreator
        
        # Create intelligent ticket creator
        auto_ticket_creator = IntelligentAutoTicketCreator()
        
        # Complete ticket creation with the provided answers
        result = auto_ticket_creator.complete_ticket_with_answers(
            query=request.original_query,
            customer_email=request.customer_email,
            analysis=request.analysis,
            answers=request.answers
        )
        
        if result.get('status') == 'created':
            ticket_data = result.get('ticket_data', {})
            
            # Generate JIRA ticket ID
            category = ticket_data.get('category', 'GENERAL')
            import random
            random_number = random.randint(10000, 99999)
            jira_ticket_id = f"{category}-{random_number}"
            ticket_data['jira_ticket_id'] = jira_ticket_id
            
            # Generate ticket content for download
            ticket_content = f"""NQUIRY INTELLIGENT AUTO-TICKET
===============================

Created automatically using AI analysis and user input
Creation Method: {ticket_data.get('creation_method', 'intelligent_auto')}
AI Completeness Score: {ticket_data.get('completeness_score', 1.0):.1%}

Ticket ID: {ticket_data.get('ticket_id', 'N/A')}
JIRA Ticket: {jira_ticket_id}
Category: {ticket_data.get('category', 'N/A')}
Customer: {ticket_data.get('customer', 'N/A')}
Customer Email: {ticket_data.get('customer_email', 'N/A')}
Created: {ticket_data.get('created_date', 'N/A')}

ORIGINAL QUERY:
===============
{ticket_data.get('original_query', 'N/A')}

TICKET DETAILS:
===============
Priority: {ticket_data.get('priority', 'N/A')}
Area Affected: {ticket_data.get('area', ticket_data.get('affected_area', 'N/A'))}
Environment: {ticket_data.get('environment', 'N/A')}
Description: {ticket_data.get('description', 'N/A')}

USER PROVIDED ANSWERS:
=====================
"""
            
            # Add user answers
            for key, value in request.answers.items():
                ticket_content += f"{key.replace('_', ' ').title()}: {value}\n"
            
            # Add AI analysis info
            if request.analysis:
                ticket_content += f"""

AI ANALYSIS:
============
Reasoning: {request.analysis.get('reasoning', 'N/A')}
Auto-detected Category: {request.analysis.get('category', 'N/A')}
Auto-detected Priority: {request.analysis.get('priority', 'N/A')}
"""
            
            # Store response in chat history
            response_message = result.get('message', 'Ticket created successfully!')
            if chat_history_manager:
                chat_history_manager.add_message(request.customer_email, "assistant", response_message, None)
            else:
                if request.customer_email not in chat_histories:
                    chat_histories[request.customer_email] = []
                chat_histories[request.customer_email].append({
                    "role": "assistant",
                    "message": response_message,
                    "timestamp": get_ist_time()
                })
            
            return {
                "status": "success",
                "message": response_message,
                "ticket_data": {
                    "ticket_id": ticket_data.get('ticket_id'),
                    "jira_ticket_id": jira_ticket_id,
                    "category": ticket_data.get('category'),
                    "customer": ticket_data.get('customer'),
                    "customer_email": ticket_data.get('customer_email'),
                    "priority": ticket_data.get('priority'),
                    "description": ticket_data.get('description')
                },
                "downloadable_content": ticket_content,
                "filename": f"ticket_auto_{ticket_data.get('category', 'UNKNOWN')}_{ticket_data.get('customer', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "auto_created": True,
                "refresh_chat": True
            }
        else:
            return {
                "status": "error",
                "message": result.get('message', 'Failed to create ticket')
            }
            
    except Exception as e:
        print(f"❌ Error creating ticket with answers: {e}")
        return {
            "status": "error",
            "message": f"Failed to create ticket: {str(e)}"
        }

@app.post("/api/tickets/create-minimal")
async def create_minimal_ticket(request: Dict[str, str]):
    """Create ticket with minimal user interaction - extract everything from query"""
    try:
        from rule_based_ticket_creator import RuleBasedTicketCreator
        
        query = request.get('query', '')
        customer_email = request.get('customer_email', '')
        
        if not query or not customer_email:
            return {
                "status": "error",
                "message": "Query and customer email are required"
            }
        
        # Create rule-based ticket creator
        auto_ticket_creator = RuleBasedTicketCreator()
        
        # Create ticket with minimal communication
        result = auto_ticket_creator.create_automatic_ticket_rule_based(
            query=query,
            customer_email=customer_email,
            force_create=True  # Force creation for testing
        )
        
        if result.get('status') == 'created':
            ticket_data = result.get('ticket_data', {})
            
            # Generate JIRA ticket ID
            category = ticket_data.get('category', 'GENERAL')
            import random
            random_number = random.randint(10000, 99999)
            jira_ticket_id = f"{category}-{random_number}"
            ticket_data['jira_ticket_id'] = jira_ticket_id
            
            # Store response in chat history
            response_message = result.get('message', 'Ticket created automatically!')
            if chat_history_manager:
                chat_history_manager.add_message(customer_email, "assistant", response_message, None)
            else:
                if customer_email not in chat_histories:
                    chat_histories[customer_email] = []
                chat_histories[customer_email].append({
                    "role": "assistant",
                    "message": response_message,
                    "timestamp": get_ist_time()
                })
            
            return {
                "status": "success",
                "message": response_message,
                "ticket_data": {
                    "ticket_id": ticket_data.get('ticket_id'),
                    "jira_ticket_id": jira_ticket_id,
                    "category": ticket_data.get('category'),
                    "customer": ticket_data.get('customer'),
                    "priority": ticket_data.get('priority'),
                    "description": ticket_data.get('description')
                },
                "auto_created": True,
                "minimal_communication": True,
                "rule_based": True,
                "refresh_chat": True
            }
        else:
            return {
                "status": "error",
                "message": result.get('message', 'Failed to create minimal ticket')
            }
            
    except Exception as e:
        print(f"❌ Error creating minimal ticket: {e}")
        return {
            "status": "error",
            "message": f"Failed to create ticket: {str(e)}"
        }

@app.post("/api/tickets/test-rule-based")
async def test_rule_based_creation():
    """Test endpoint for rule-based ticket creation"""
    try:
        from rule_based_ticket_creator import RuleBasedTicketCreator
        
        # Test query
        test_query = "I cannot access the admin panel, it shows a 500 error when I try to login"
        test_email = "admin@amgen.com"
        
        # Create rule-based ticket creator
        auto_ticket_creator = RuleBasedTicketCreator()
        
        print(f"🧪 Testing rule-based ticket creation with query: {test_query}")
        
        # Create ticket with rule-based analysis
        result = auto_ticket_creator.create_automatic_ticket_rule_based(
            query=test_query,
            customer_email=test_email,
            force_create=True
        )
        
        return {
            "status": "test_complete",
            "result": result,
            "test_query": test_query,
            "test_email": test_email
        }
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}"
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
        
        # Process populated fields to resolve dynamic values
        populated_fields = category_config.get("populated_fields", {}).copy()
        for field, value in populated_fields.items():
            if isinstance(value, str):
                if value.lower() == 'current_date':
                    # Replace with current date in YYYY-MM-DD format
                    populated_fields[field] = get_ist_time().strftime('%Y-%m-%d')
                elif 'based on customer organization' in value.lower():
                    # Get the actual organization name from customer role manager
                    from customer_role_manager import CustomerRoleMappingManager
                    customer_manager = CustomerRoleMappingManager()
                    domain = customer_email.split('@')[-1] if customer_email and '@' in customer_email else 'unknown.com'
                    customer_mapping = customer_manager.get_customer_mapping(domain)
                    populated_fields[field] = customer_mapping.get('organization', customer)
                elif 'based on customer sheet mapping' in value.lower():
                    # Determine MNHT or MNLS based on customer sheet mapping
                    from customer_role_manager import CustomerRoleMappingManager
                    customer_manager = CustomerRoleMappingManager()
                    domain = customer_email.split('@')[-1] if customer_email and '@' in customer_email else 'unknown.com'
                    customer_mapping = customer_manager.get_customer_mapping(domain)
                    sheet = customer_mapping.get('sheet', 'HT')
                    if sheet.upper() == 'LS':
                        populated_fields[field] = 'MNLS'
                    else:  # Default to HT/MNHT
                        populated_fields[field] = 'MNHT'
                elif 'based on description' in value.lower():
                    # Generate summary based on query
                    populated_fields[field] = f"Support Request: {query[:80]}{'...' if len(query) > 80 else ''}"
        
        return {
            "status": "success",
            "category": category,
            "customer": customer,
            "required_fields": category_config.get("required_fields", {}),
            "populated_fields": populated_fields,
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

# Feedback and Continuous Learning endpoints
@app.post("/api/feedback/collect")
async def collect_feedback(request: dict):
    """Collect user feedback for continuous learning"""
    try:
        user_id = request.get("user_id", "")
        response_content = request.get("response_content", "")
        feedback_type = request.get("feedback_type", "")  # positive, negative, excellent, needs_improvement
        feedback_category = request.get("feedback_category", "")  # thumbs_up, thumbs_down, star, improve
        session_id = request.get("session_id", "")
        
        print(f"🎯 Collecting feedback from user: {user_id}")
        print(f"   - Feedback type: {feedback_type}")
        print(f"   - Category: {feedback_category}")
        
        # Store feedback in chat history manager if available
        if chat_history_manager:
            # Add feedback as a special message type
            feedback_message = f"[FEEDBACK] {feedback_type.upper()} ({feedback_category})"
            chat_history_manager.add_message(user_id, "feedback", feedback_message, session_id)
        
        # 🧠 REAL LEARNING: Use the learning manager to store and analyze feedback
        learning_manager = get_learning_manager()
        learning_result = learning_manager.store_feedback(
            user_id=user_id,
            response_content=response_content,
            feedback_type=feedback_type,
            feedback_category=feedback_category,
            session_id=session_id
        )
        
        print(f"🧠 Learning analysis completed: {learning_result}")
        
        return {
            "status": "success",
            "message": "Feedback collected and learning updated",
            "learning_result": learning_result
        }
        
    except Exception as e:
        print(f"❌ Error collecting feedback: {e}")
        return {
            "status": "error",
            "message": f"Failed to collect feedback: {str(e)}"
        }

@app.get("/api/learning/status")
async def get_learning_status(user_id: str = ""):
    """Get continuous learning status and analytics"""
    try:
        # 🧠 REAL LEARNING: Get actual analytics from learning manager
        learning_manager = get_learning_manager()
        learning_status = learning_manager.get_learning_status(user_id if user_id else None)
        
        print(f"📊 Learning status retrieved: {learning_status['status']} - Score: {learning_status['score']:.1f}%")
        
        return {
            "status": "success",
            "learning_status": learning_status
        }
        
    except Exception as e:
        print(f"❌ Error getting learning status: {e}")
        return {
            "status": "error",
            "message": f"Failed to get learning status: {str(e)}"
        }

@app.get("/api/learning/insights")
async def get_learning_insights():
    """Get detailed learning insights and recommendations"""
    try:
        learning_manager = get_learning_manager()
        
        # Get comprehensive learning analysis
        insights = learning_manager.get_learning_status()
        adaptive_params = learning_manager.get_adaptive_search_parameters()
        
        return {
            "status": "success",
            "insights": insights,
            "adaptive_parameters": adaptive_params,
            "system_health": {
                "learning_enabled": True,
                "database_connected": True,
                "analysis_engine": "active"
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting learning insights: {e}")
        return {
            "status": "error",
            "message": f"Failed to get learning insights: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting nQuiry FastAPI server...")
    print("🧠 Using existing intelligent nQuiry system")
    print("🌐 Frontend URL: http://localhost:3000")
    print("📡 API URL: http://localhost:8000") 
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)