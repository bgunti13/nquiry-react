"""
nQuiry - Intelligent Query Processing Chatbot
Streamlit Web Interface
"""

import streamlit as st
import time
from datetime import datetime
from main import IntelligentQueryProcessor
from chat_history_manager import ChatHistoryManager
import traceback

# Configure the Streamlit page
st.set_page_config(
    page_title="nQuiry - Intelligent Query Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
def get_theme_css(dark_mode=True):
    """Generate CSS based on theme mode"""
    if dark_mode:
        # Dark mode colors
        theme_vars = {
            'primary_color': '#1f77b4',
            'secondary_color': '#ff7f0e',
            'background_color': '#0e1117',
            'text_color': '#ffffff',
            'border_color': '#30363d',
            'card_bg': '#161b22',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2',
            'chat_user_bg': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'chat_bot_bg': 'linear-gradient(135deg, #21262d 0%, #30363d 100%)',
            'chat_bot_text': '#ffffff',
            'header_bg': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'sidebar_bg': '#0d1117',
            'input_bg': '#21262d',
            'input_border': '#30363d'
        }
    else:
        # Light mode colors
        theme_vars = {
            'primary_color': '#0066cc',
            'secondary_color': '#ff6b35',
            'background_color': '#ffffff',
            'text_color': '#2c3e50',
            'border_color': '#dee2e6',
            'card_bg': '#ffffff',
            'gradient_start': '#74b9ff',
            'gradient_end': '#0984e3',
            'chat_user_bg': 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
            'chat_bot_bg': 'linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%)',
            'chat_bot_text': '#2c3e50',
            'header_bg': 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
            'sidebar_bg': '#f8f9fa',
            'input_bg': '#ffffff',
            'input_border': '#ced4da'
        }
    
    return f"""
<style>
    /* Main theme colors */
    :root {{
        --primary-color: {theme_vars['primary_color']};
        --secondary-color: {theme_vars['secondary_color']};
        --background-color: {theme_vars['background_color']};
        --text-color: {theme_vars['text_color']};
        --border-color: {theme_vars['border_color']};
    }}

    /* Hide default Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Main app background */
    .stApp {{
        background-color: {theme_vars['background_color']};
        color: {theme_vars['text_color']};
    }}
    
    /* Main content area */
    .main .block-container {{
        background-color: {theme_vars['background_color']};
        color: {theme_vars['text_color']};
        padding-top: 1rem;
    }}
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {{
        background-color: {theme_vars['sidebar_bg']};
    }}
    
    .css-1d391kg .css-10trblm {{
        color: {theme_vars['text_color']};
    }}
    
    /* Sidebar text and headers */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {{
        color: {theme_vars['text_color']};
    }}
    
    .css-1d391kg .css-10trblm {{
        color: {theme_vars['text_color']};
    }}
    
    /* Main container styling */
    .main-container {{
        background: {theme_vars['header_bg']};
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }}
    
    /* Title styling */
    .main-title {{
        color: white;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .main-subtitle {{
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 300;
    }}
    
    /* Chat container */
    .chat-container {{
        background: {theme_vars['card_bg']};
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid {theme_vars['border_color']};
    }}
    
    /* Message styling */
    .user-message {{
        background: {theme_vars['chat_user_bg']};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease-out;
    }}
    
    .bot-message {{
        background: {theme_vars['chat_bot_bg']};
        color: {theme_vars['chat_bot_text']};
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0;
        border-left: 4px solid {theme_vars['primary_color']};
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        animation: slideInLeft 0.3s ease-out;
    }}
    
    /* Status indicators */
    .status-indicator {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }}
    
    .status-online {{ background-color: #28a745; }}
    .status-offline {{ background-color: #dc3545; }}
    .status-processing {{ background-color: #ffc107; }}
    
    /* Animations */
    @keyframes slideInRight {{
        from {{ opacity: 0; transform: translateX(30px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    @keyframes slideInLeft {{
        from {{ opacity: 0; transform: translateX(-30px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
        100% {{ opacity: 1; }}
    }}
    
    .processing {{
        animation: pulse 1.5s infinite;
    }}
    
    /* Input styling */
    .stTextInput > div > div > input {{
        border-radius: 25px;
        border: 2px solid {theme_vars['input_border']};
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        background-color: {theme_vars['input_bg']};
        color: {theme_vars['text_color']};
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {theme_vars['primary_color']};
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div > select {{
        background-color: {theme_vars['input_bg']};
        color: {theme_vars['text_color']};
        border: 1px solid {theme_vars['input_border']};
    }}
    
    /* Button styling */
    .stButton > button {{
        background: {theme_vars['chat_user_bg']};
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }}
    
    /* Sidebar button styling */
    .css-1d391kg .stButton > button {{
        background: {theme_vars['primary_color']};
        color: white;
        border: 1px solid {theme_vars['border_color']};
        border-radius: 10px;
        margin: 0.25rem 0;
    }}
    
    .css-1d391kg .stButton > button:hover {{
        background: {theme_vars['secondary_color']};
        transform: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    
    /* Expander styling */
    .streamlit-expanderHeader {{
        background-color: {theme_vars['card_bg']};
        color: {theme_vars['text_color']};
        border: 1px solid {theme_vars['border_color']};
    }}
    
    .streamlit-expanderContent {{
        background-color: {theme_vars['card_bg']};
        color: {theme_vars['text_color']};
        border: 1px solid {theme_vars['border_color']};
    }}
    
    /* Theme toggle button */
    .theme-toggle {{
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        background: {theme_vars['primary_color']};
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 1.2rem;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }}
    
    .theme-toggle:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }}
    
    /* Markdown text styling */
    .css-1d391kg .markdown-text-container p {{
        color: {theme_vars['text_color']};
    }}
    
    /* Caption styling */
    .css-1d391kg .css-10trblm small {{
        color: {theme_vars['text_color']};
        opacity: 0.7;
    }}
</style>
"""

st.markdown(get_theme_css(st.session_state.get('dark_mode', True)), unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'nquiry_processor' not in st.session_state:
        st.session_state.nquiry_processor = None
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'customer_info' not in st.session_state:
        st.session_state.customer_info = None
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = None
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True  # Default to dark mode

def load_specific_conversation(user_id, conversation_index):
    """Load a specific conversation from MongoDB history"""
    try:
        if not st.session_state.chat_manager:
            st.session_state.chat_manager = ChatHistoryManager()
        
        # Get full chat history from MongoDB
        mongo_history = st.session_state.chat_manager.get_history(user_id)
        
        # Convert MongoDB format to Streamlit format
        full_chat_history = []
        for msg in mongo_history:
            msg_type = 'bot' if msg['role'] == 'assistant' else msg['role']
            full_chat_history.append({
                'type': msg_type,
                'content': msg['message'],
                'timestamp': msg['timestamp'].strftime("%H:%M") if hasattr(msg['timestamp'], 'strftime') else str(msg.get('timestamp', ''))
            })
        
        # Group messages into conversations (split by time gaps or conversation boundaries)
        conversations = []
        current_conversation = []
        
        for i, msg in enumerate(full_chat_history):
            current_conversation.append(msg)
            
            # End conversation if this is a bot message and next message is far apart in time
            # or if we reach the end
            if (msg['type'] == 'bot' and 
                (i == len(full_chat_history) - 1 or  # Last message
                 i < len(full_chat_history) - 1)):  # Or there's a next message
                conversations.append(current_conversation.copy())
                current_conversation = []
        
        # Load the specific conversation
        if 0 <= conversation_index < len(conversations):
            st.session_state.chat_history = conversations[conversation_index]
            return True
        
        return False
    except Exception as e:
        print(f"Error loading specific conversation: {e}")
        return False

def load_chat_history_for_user(user_id):
    """Load chat history from MongoDB for the user"""
    try:
        if not st.session_state.chat_manager:
            st.session_state.chat_manager = ChatHistoryManager()
        
        # Get chat history from MongoDB
        mongo_history = st.session_state.chat_manager.get_history(user_id)
        print(f"DEBUG: Retrieved {len(mongo_history)} messages from MongoDB for user {user_id}")
        
        # Convert MongoDB format to Streamlit format
        chat_history = []
        for msg in mongo_history:
            # Convert 'assistant' role to 'bot' for Streamlit UI
            msg_type = 'bot' if msg['role'] == 'assistant' else msg['role']
            # MongoDB stores content as 'message', not 'content'
            content = msg.get('message', msg.get('content', ''))
            converted_msg = {
                'type': msg_type,
                'content': content,
                'timestamp': msg['timestamp'].strftime("%H:%M") if hasattr(msg['timestamp'], 'strftime') else msg.get('timestamp', '')
            }
            chat_history.append(converted_msg)
            print(f"DEBUG: Converted message - Type: {msg_type}, Content: {content[:50]}...")
        
        st.session_state.chat_history = chat_history
        print(f"DEBUG: Set session state with {len(chat_history)} messages")
        return True
    except Exception as e:
        print(f"Error loading chat history: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_conversation_by_question(user_id, question):
    """Load the conversation that contains a specific question"""
    try:
        if not st.session_state.chat_manager:
            st.session_state.chat_manager = ChatHistoryManager()
        
        # Get full chat history from MongoDB
        mongo_history = st.session_state.chat_manager.get_history(user_id)
        print(f"DEBUG: Looking for question: '{question}' in {len(mongo_history)} messages")
        
        # Find the conversation that contains this question
        conversation_messages = []
        found_question = False
        
        for i, msg in enumerate(mongo_history):
            if msg['role'] == 'user' and msg['message'].strip() == question.strip():
                found_question = True
                print(f"DEBUG: Found exact match at index {i}")
                # Start collecting messages from this question
                conversation_messages = []
                
                # Add the question
                conversation_messages.append(msg)
                print(f"DEBUG: Added user question: {msg['message'][:50]}...")
                
                # Add all subsequent assistant responses for this question
                for j in range(i + 1, len(mongo_history)):
                    next_msg = mongo_history[j]
                    if next_msg['role'] == 'assistant':
                        conversation_messages.append(next_msg)
                        print(f"DEBUG: Added assistant response: {next_msg['message'][:50]}...")
                    elif next_msg['role'] == 'user':
                        # Check if it's the same question (duplicate) - if so, skip it
                        if next_msg['message'].strip() == question.strip():
                            print(f"DEBUG: Skipping duplicate user question at index {j}")
                            continue
                        else:
                            # Different user question - stop here
                            print(f"DEBUG: Stopped at different user question at index {j}")
                            break
                print(f"DEBUG: Collected {len(conversation_messages)} messages for this conversation")
                break
        
        if found_question:
            print(f"DEBUG: Found conversation with {len(conversation_messages)} messages")
            # Convert to Streamlit format
            chat_history = []
            for msg in conversation_messages:
                msg_type = 'bot' if msg['role'] == 'assistant' else msg['role']
                content = msg['message']
                chat_history.append({
                    'type': msg_type,
                    'content': content,
                    'timestamp': msg['timestamp'].strftime("%H:%M") if hasattr(msg['timestamp'], 'strftime') else str(msg.get('timestamp', ''))
                })
                print(f"DEBUG: Converted message - Type: {msg_type}, Content length: {len(content)}, Content: '{content[:100]}{'...' if len(content) > 100 else ''}'")
            
            st.session_state.chat_history = chat_history
            print(f"DEBUG: Set session state with {len(chat_history)} messages")
            print(f"DEBUG: Session chat history now contains:")
            for i, msg in enumerate(st.session_state.chat_history):
                print(f"  {i+1}. {msg['type']}: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")
            return True
        else:
            print(f"DEBUG: Question not found: '{question}'")
        
        return False
    except Exception as e:
        print(f"Error loading conversation by question: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_past_conversations(user_id):
    """Get past conversations grouped for sidebar display"""
    try:
        if not st.session_state.chat_manager:
            st.session_state.chat_manager = ChatHistoryManager()
        
        # Get full chat history from MongoDB
        mongo_history = st.session_state.chat_manager.get_history(user_id)
        
        # Get unique user questions only (for sidebar display)
        unique_questions = []
        seen_questions = set()
        
        for msg in mongo_history:
            if msg['role'] == 'user':
                question = msg['message']
                if question not in seen_questions:
                    unique_questions.append({
                        'content': question,
                        'timestamp': msg['timestamp'].strftime("%H:%M") if hasattr(msg['timestamp'], 'strftime') else str(msg.get('timestamp', ''))
                    })
                    seen_questions.add(question)
        
        return unique_questions[-5:]  # Return last 5 unique questions
    except Exception as e:
        print(f"Error getting past conversations: {e}")
        return []

def save_message_to_history(user_id, role, content):
    """Save a message to MongoDB"""
    try:
        if not st.session_state.chat_manager:
            st.session_state.chat_manager = ChatHistoryManager()
        
        # ChatHistoryManager expects 'message' parameter, not 'content'
        st.session_state.chat_manager.add_message(user_id, role, content)
        return True
    except Exception as e:
        print(f"Error saving message: {e}")
        return False

def display_header():
    """Display the main header with user info"""
    customer_info = st.session_state.customer_info or {}
    
    # Create header with user info
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        # Organization and Role (top left) - removed to avoid duplication
        pass
    
    with col2:
        # Main title (center)
        st.markdown("""
        <div class="main-container">
            <h1 class="main-title">🔍 Nquiry</h1>
            <p class="main-subtitle">Intelligent Customer Assistant</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # User name (top right)
        if customer_info:
            email = customer_info.get('email', 'Unknown')
            user_name = email.split('@')[0] if email != 'Unknown' else 'User'
            st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 0.3rem 0.8rem;
                border-radius: 8px;
                margin-top: 1rem;
                color: white;
                font-size: 0.8rem;
                text-align: right;
                display: inline-block;
                float: right;
            ">
                👤 {user_name}
            </div>
            """, unsafe_allow_html=True)

def display_system_status():
    """Display system status in sidebar"""
    
    # Theme toggle button
    st.sidebar.markdown("### 🎨 Theme")
    
    theme_icon = "🌙" if st.session_state.dark_mode else "☀️"
    theme_text = "Switch to Light Mode" if st.session_state.dark_mode else "Switch to Dark Mode"
    
    if st.sidebar.button(f"{theme_icon} {theme_text}", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    
    st.sidebar.markdown("---")  # Add separator
    
    st.sidebar.markdown("### 👤 Customer Info")
    
    if st.session_state.nquiry_processor:
        try:
            # Get system status from the processor
            processor = st.session_state.nquiry_processor
            customer_info = st.session_state.customer_info or {}
            
            # Display customer info
            org = customer_info.get('organization', 'Unknown')
            role = customer_info.get('role', 'Unknown')
            email = customer_info.get('email', 'Unknown')
            
            st.sidebar.markdown(f"""
            - 🏢 **Organization:** `{org}`
            - 🎭 **Role:** `{role}`
            """)
            
            # Recent Chat History Dropdown
            st.sidebar.markdown("### 💬 Recent Chat History")
            
            # Get user ID for chat history
            user_id = customer_info.get('email', 'demo_user') if customer_info else 'demo_user'
            
            # Get past conversations for sidebar
            past_conversations = get_past_conversations(user_id)
            
            if past_conversations:
                with st.sidebar.expander(f"Recent Conversations ({len(past_conversations)})", expanded=False):
                    for i, conv in enumerate(past_conversations):
                        timestamp = conv.get('timestamp', '')
                        content = conv['content'][:45] + "..." if len(conv['content']) > 45 else conv['content']
                        
                        # Make each conversation clickable
                        if st.button(
                            f"💬 {content}",
                            key=f"conv_{i}_{timestamp}",
                            help=f"Click to load this conversation from {timestamp}",
                            use_container_width=True
                        ):
                            # Find the full conversation that contains this question
                            if load_conversation_by_question(user_id, conv['content']):
                                st.success(f"✅ Loaded conversation: {content}")
                                st.rerun()
                            else:
                                st.error("❌ Could not load conversation")
                        
                        st.caption(f"⏰ {timestamp}")
                        if i < len(past_conversations) - 1:
                            st.divider()
            else:
                with st.sidebar.expander("Recent Conversations", expanded=False):
                    st.write("No past conversations found")
                    st.caption("Start a conversation to see history")
            
            # Start New Conversation Button
            st.sidebar.markdown("---")  # Add separator
            if st.sidebar.button("🆕 Start New Conversation", use_container_width=True, type="primary"):
                # Clear current chat history to start fresh
                st.session_state.chat_history = []
                st.success("✅ Started new conversation!")
                st.rerun()
            
            st.sidebar.markdown("---")  # Add separator
            
            # Recent Tickets Dropdown
            st.sidebar.markdown("### 🎫 Recent Tickets")
            
            # Show empty state for dummy customers
            with st.sidebar.expander("Recent Support Tickets", expanded=False):
                st.write("No recent support tickets found")
                st.caption("� Support tickets will appear here once available")
                
        except Exception as e:
            st.sidebar.error(f"Info unavailable: {e}")
    else:
        st.sidebar.info("Please initialize system first")

def initialize_nquiry():
    """Initialize nQuiry processor"""
    if not st.session_state.initialized:
        try:
            with st.spinner("🚀 Initializing nQuiry system..."):
                # Create a placeholder for the email input since we can't use input() in Streamlit
                # We'll handle this differently in the Streamlit app
                st.session_state.nquiry_processor = "placeholder"  # Will be created when customer email is provided
                st.session_state.initialized = True
                st.success("✅ nQuiry system ready!")
        except Exception as e:
            st.error(f"❌ Failed to initialize nQuiry: {e}")
            st.exception(e)

def create_nquiry_processor(customer_email):
    """Create nQuiry processor with customer email"""
    try:
        # Temporarily patch the input function to return our email
        import builtins
        original_input = builtins.input
        builtins.input = lambda prompt="": customer_email
        
        try:
            processor = IntelligentQueryProcessor()
            st.session_state.customer_info = processor.customer_info
            
            # Start with fresh conversation - don't load old history automatically
            # User can access old conversations through Recent Chat History sidebar
            st.session_state.chat_history = []  # Fresh conversation
            st.session_state.history_loaded = True  # Mark as initialized
            
            return processor
        finally:
            # Restore original input function
            builtins.input = original_input
            
    except Exception as e:
        st.error(f"Failed to create processor: {e}")
        return None

def display_chat_history():
    """Display chat history with proper markdown rendering"""
    for message in st.session_state.chat_history:
        timestamp = message.get('timestamp', '')
        
        if message['type'] == 'user':
            # User message container
            with st.container():
                st.markdown("""
                <div style="
                    display: flex; 
                    justify-content: flex-end; 
                    margin: 1rem 0;
                ">
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 1rem 1.5rem;
                        border-radius: 20px 20px 5px 20px;
                        max-width: 70%;
                        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
                    ">
                        <div style="font-weight: bold; margin-bottom: 0.5rem;">
                            You <small style="opacity:0.7; font-weight: normal;">({timestamp})</small>
                        </div>
                        <div>{content}</div>
                    </div>
                </div>
                """.format(content=message['content'], timestamp=timestamp), unsafe_allow_html=True)
        
        else:
            # Bot message container with proper markdown rendering
            with st.container():
                st.markdown("""
                <div style="
                    display: flex; 
                    justify-content: flex-start; 
                    margin: 1rem 0;
                ">
                    <div style="
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                        color: #2c3e50;
                        padding: 1rem 1.5rem;
                        border-radius: 20px 20px 20px 5px;
                        max-width: 80%;
                        border-left: 4px solid #1f77b4;
                        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                    ">
                        <div style="font-weight: bold; margin-bottom: 0.5rem; color: #1f77b4;">
                            🔍 nQuiry <small style="opacity:0.7; font-weight: normal;">({timestamp})</small>
                        </div>
                    </div>
                </div>
                """.format(timestamp=timestamp), unsafe_allow_html=True)
                
                # Render the actual response content as markdown in a separate container
                with st.container():
                    # Parse the response if it's a dictionary string
                    content = message['content']
                    if isinstance(content, str) and content.startswith("{") and "response" in content:
                        try:
                            import ast
                            response_dict = ast.literal_eval(content)
                            if 'response' in response_dict and response_dict['response']:
                                # Display the formatted markdown response
                                st.markdown(response_dict['response'])
                                
                                # Show additional info if available
                                if response_dict.get('results_found', 0) > 0:
                                    st.info(f"ℹ️ Found {response_dict['results_found']} relevant result(s)")
                            else:
                                st.write(content)
                        except Exception as e:
                            # Fallback to raw content if parsing fails
                            st.markdown(content)
                    else:
                        # If it's already markdown text, render it directly
                        st.markdown(content)
                    
                    # Add some spacing
                    st.markdown("<br>", unsafe_allow_html=True)

def process_query(query, processor, user_id):
    """Process user query and return response"""
    try:
        with st.spinner("🔍 Processing your query..."):
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate processing stages
            status_text.text("🎫 Searching JIRA...")
            progress_bar.progress(25)
            time.sleep(0.5)
            
            status_text.text("📄 Searching MindTouch...")
            progress_bar.progress(50)
            time.sleep(0.5)
            
            status_text.text("🔍 Processing results...")
            progress_bar.progress(75)
            time.sleep(0.5)
            
            # Get chat history for context
            history = []
            if hasattr(processor, 'chat_history_manager'):
                history = processor.chat_history_manager.get_history(user_id)
            
            # Actually process the query, passing history for context
            result = processor.process_query(user_id, query, history=history)
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Extract the actual response content from the result
            if isinstance(result, dict):
                # If result is a dictionary, extract the response
                if 'response' in result and result['response']:
                    return result['response']
                elif 'formatted_response' in result and result['formatted_response']:
                    return result['formatted_response']
                elif 'ticket_created' in result and result['ticket_created']:
                    return f"🎫 **Ticket Created Successfully**\n\n{result['ticket_created']}"
                else:
                    return "❌ Sorry, I couldn't find a relevant response to your query."
            else:
                # If result is a string, return as-is
                return result if result else "❌ Sorry, I couldn't process your query."
            
    except Exception as e:
        st.error(f"Error processing query: {e}")
        return f"❌ Sorry, I encountered an error: {str(e)}"

def main():
    """Main Streamlit app"""
    initialize_session_state()
    display_header()
    
    # Sidebar
    display_system_status()
    
    # Customer email input (only if not initialized)
    if not st.session_state.nquiry_processor or st.session_state.nquiry_processor == "placeholder":
        st.markdown("### 🔐 Customer Authentication")
        
        with st.form("customer_auth"):
            customer_email = st.text_input(
                "Please enter your email for customer identification:",
                placeholder="your.email@company.com",
                help="This is required for role-based access to JIRA and MindTouch"
            )
            
            if st.form_submit_button("🚀 Initialize nQuiry", use_container_width=True):
                if customer_email:
                    with st.spinner("Initializing nQuiry with your credentials..."):
                        processor = create_nquiry_processor(customer_email)
                        if processor:
                            st.session_state.nquiry_processor = processor
                            st.success("✅ nQuiry initialized successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to initialize nQuiry")
                else:
                    st.warning("Please enter your email address")
        return
    
    # Main chat interface
    st.markdown("### 💬 Chat with nQuiry")
    
    # Display chat history
    display_chat_history()
    
    # Query input
    with st.form("query_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_query = st.text_input(
                "Ask me anything:",
                placeholder="How do I reset my password?",
                label_visibility="collapsed"
            )
        
        with col2:
            submit_button = st.form_submit_button("Send 🚀", use_container_width=True)
    
    # Process query if submitted
    if submit_button and user_query:
        # Get user ID for MongoDB
        user_id = st.session_state.customer_info.get('email', 'demo_user') if st.session_state.customer_info else 'demo_user'
        
        # Add user message to chat history
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.chat_history.append({
            'type': 'user',
            'content': user_query,
            'timestamp': timestamp
        })
        
        # Save user message to MongoDB
        save_message_to_history(user_id, 'user', user_query)
        
        # Process query
        if st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
            response = process_query(user_query, st.session_state.nquiry_processor, user_id)
            print(f"DEBUG STREAMLIT: Received response of length {len(response)}: {response[:100]}...")
            
            # Add bot response to chat history
            bot_timestamp = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append({
                'type': 'bot',
                'content': response,
                'timestamp': bot_timestamp
            })
            
            # Note: Bot response is already saved to MongoDB by the processor.process_query() method
            # No need to save again here to avoid duplicates
        else:
            st.error("nQuiry processor not initialized")
        
        # Rerun to update the display
        st.rerun()
    
    # Example queries below chat box
    st.markdown("---")
    st.markdown("### 💡 Try These Example Queries")
    
    example_queries = [
        "How do I reset my password?",
        "What are the system requirements?", 
        "How do I submit a bug report?",
        "Who should I contact for support?",
        "How do I update my profile?"
    ]
    
    # Display example queries in columns for better layout
    cols = st.columns(2)
    for i, query in enumerate(example_queries):
        with cols[i % 2]:
            if st.button(f"💬 {query}", key=f"example_{query}", use_container_width=True):
                # Get user ID for MongoDB
                user_id = st.session_state.customer_info.get('email', 'demo_user') if st.session_state.customer_info else 'demo_user'
                
                # Add to chat and process
                timestamp = datetime.now().strftime("%H:%M")
                st.session_state.chat_history.append({
                    'type': 'user',
                    'content': query,
                    'timestamp': timestamp
                })
                
                # Save user message to MongoDB
                save_message_to_history(user_id, 'user', query)
                
                if st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
                    response = process_query(query, st.session_state.nquiry_processor, user_id)
                    bot_timestamp = datetime.now().strftime("%H:%M")
                    st.session_state.chat_history.append({
                        'type': 'bot',
                        'content': response,
                        'timestamp': bot_timestamp
                    })
                    
                    # Note: Bot response is already saved to MongoDB by the processor.process_query() method
                    # No need to save again here to avoid duplicates
                
                st.rerun()
    
    # Clear chat button in sidebar
    if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
        # Clear both session state and MongoDB history
        user_id = st.session_state.customer_info.get('email', 'demo_user') if st.session_state.customer_info else 'demo_user'
        
        # Clear MongoDB history
        if st.session_state.chat_manager:
            try:
                st.session_state.chat_manager.clear_history(user_id)
            except Exception as e:
                print(f"Error clearing MongoDB history: {e}")
        
        # Clear session state
        st.session_state.chat_history = []
        st.session_state.history_loaded = False
        st.rerun()

if __name__ == "__main__":
    main()
