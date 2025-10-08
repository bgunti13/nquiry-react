"""
nQuiry - Intelligent Query Processing Chatbot
Streamlit Web Interface
"""

import streamlit as st
import time
from datetime import datetime
from datetime import timezone
from main import IntelligentQueryProcessor
from chat_history_manager import ChatHistoryManager
import traceback

# Import voice input functionality
try:
    from voice_input import create_voice_input_component, add_voice_tips, speak_response
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    st.error(f"Voice input not available: {e}")

# Configure the Streamlit page
st.set_page_config(
    page_title="nQuiry - Intelligent Query Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
def get_theme_css():
    """Generate CSS for light mode theme"""
    # Light mode colors - subtle and professional
    theme_vars = {
        'primary_color': '#2563eb',
        'secondary_color': '#059669', 
        'background_color': '#fafbfc',
        'text_color': '#1f2937',
        'border_color': '#e5e7eb',
        'card_bg': '#ffffff',
        'gradient_start': '#e0f2fe',
        'gradient_end': '#bae6fd',
        'chat_user_bg': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
        'chat_bot_bg': '#f8fafc',
        'chat_bot_text': '#374151',
        'header_bg': 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
        'header_text': '#333333',
        'sidebar_bg': '#e8e8e8',
        'sidebar_text': '#1f2937',
        'input_bg': '#ffffff',
        'input_border': '#d1d5db',
        'button_hover': '#1d4ed8',
        'accent_color': '#6366f1'
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
    
    /* Ensure all main content text is dark */
    .main * {{
        color: {theme_vars['text_color']};
    }}
    
    /* Headers and text in main area */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {{
        color: {theme_vars['text_color']};
    }}
    
    .main p, .main div, .main span {{
        color: {theme_vars['text_color']};
    }}
    
    /* AGGRESSIVE SIDEBAR VISIBILITY - Override all Streamlit hiding */
    section[data-testid="stSidebar"] {{
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: translateX(0px) !important;
        position: relative !important;
        left: 0px !important;
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
        background-color: #DCDCDC !important;
        z-index: 999999 !important;
    }}
    
    /* Force sidebar container to be visible */
    .css-1d391kg {{
        display: block !important;
        visibility: visible !important;
        background-color: #DCDCDC !important;
    }}
    
    .css-1lcbmhc {{
        display: block !important;
        visibility: visible !important;
        background-color: #DCDCDC !important;
    }}
    
    /* Hide ALL possible collapse controls */
    button[kind="header"][data-testid="collapsedControl"],
    button[data-testid="collapsedControl"],
    .css-1dp5vir,
    [data-testid="stSidebar"] button[aria-label*="collapse"],
    [data-testid="stSidebar"] button[aria-label*="Close"],
    [data-testid="stSidebar"] button[aria-label*="open"],
    [data-testid="stSidebar"] button[aria-label*="hide"],
    [data-testid="stSidebar"] .css-1rs6os {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* Force main content to leave space for sidebar */
    .main .block-container {{
        margin-left: 300px !important;
        padding-left: 1rem !important;
    }}
    
    /* Override any collapsed state */
    section[data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="true"],
    section[data-testid="stSidebar"] {{
        display: block !important;
        visibility: visible !important;
        transform: translateX(0px) !important;
        left: 0px !important;
        width: 280px !important;
        background-color: #DCDCDC !important;
    }}
    
    /* Sidebar content styling */
    section[data-testid="stSidebar"] > div:first-child {{
        background-color: #DCDCDC !important;
        display: block !important;
        visibility: visible !important;
    }}
    
    /* Target all sidebar elements */
    section[data-testid="stSidebar"] * {{
        background-color: #DCDCDC !important;
    }}
    
    /* Specifically target sidebar containers and boxes */
    section[data-testid="stSidebar"] .element-container {{
        background-color: #DCDCDC !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown {{
        background-color: #DCDCDC !important;
    }}
    
    section[data-testid="stSidebar"] .stExpander {{
        background-color: #DCDCDC !important;
        border: none !important;
    }}
    
    section[data-testid="stSidebar"] .stExpander > div {{
        background-color: #DCDCDC !important;
    }}
    
    section[data-testid="stSidebar"] .stButton {{
        background-color: #DCDCDC !important;
    }}
    
    section[data-testid="stSidebar"] .stButton > button {{
        background-color: #e8e8e8 !important;
        border: 1px solid #d0d0d0 !important;
        color: #333333 !important;
    }}
    
    /* Target button text specifically */
    section[data-testid="stSidebar"] .stButton > button > div {{
        background-color: transparent !important;
    }}
    
    /* Target all text elements in sidebar */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        background-color: transparent !important;
        background: transparent !important;
    }}
    
    /* Remove any white backgrounds from text containers */
    section[data-testid="stSidebar"] [data-testid] {{
        background-color: #DCDCDC !important;
    }}
    
    section[data-testid="stSidebar"] [data-testid] * {{
        background-color: transparent !important;
    }}
    
    .css-1d391kg, .css-1lcbmhc {{
        background-color: #DCDCDC !important;
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div {{
        min-width: 150px !important;
    }}
    
    .stSelectbox > div > div > div {{
        padding: 0.5rem 1rem !important;
    }}
    
    /* Sidebar content container */
    section[data-testid="stSidebar"] > div {{
        display: block !important;
        visibility: visible !important;
    }}
    
    .css-1d391kg .css-10trblm {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Sidebar text and headers */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Additional sidebar text styling */
    section[data-testid="stSidebar"] .stMarkdown {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    section[data-testid="stSidebar"] label {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Force all sidebar elements to have dark text */
    section[data-testid="stSidebar"] * {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Override any white text in sidebar except buttons */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stText {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Keep button text white since buttons have dark backgrounds */
    section[data-testid="stSidebar"] .stButton button {{
        color: white !important;
    }}
    
    .css-1d391kg .css-10trblm {{
        color: {theme_vars['sidebar_text']} !important;
    }}
    
    /* Main container styling */
    .main-container {{
        background: {theme_vars['header_bg']};
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid {theme_vars['border_color']};
    }}
    
    /* Title styling */
    .main-title {{
        color: {theme_vars['header_text']};
        font-size: 1.2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.3rem;
    }}
    
    .main-subtitle {{
        color: {theme_vars['text_color']};
        opacity: 0.8;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 400;
    }}
    
    /* Chat container */
    .chat-container {{
        background: {theme_vars['card_bg']};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin: 1rem 0;
        border: 1px solid {theme_vars['border_color']};
    }}
    
    /* Message styling */
    .user-message {{
        background: {theme_vars['chat_bot_bg']};
        color: {theme_vars['chat_bot_text']};
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        border-left: 3px solid {theme_vars['accent_color']};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        animation: slideInRight 0.3s ease-out;
        line-height: 1.6;
        font-size: 14px;
        border: 1px solid {theme_vars['border_color']};
    }}
    
    .bot-message {{
        background: {theme_vars['chat_bot_bg']};
        color: {theme_vars['chat_bot_text']};
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        border-left: 3px solid {theme_vars['accent_color']};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        animation: slideInLeft 0.3s ease-out;
        line-height: 1.6;
        font-size: 14px;
        border: 1px solid {theme_vars['border_color']};
    }}
    
    /* Override markdown formatting in bot messages */
    .bot-message h1, 
    .bot-message h2, 
    .bot-message h3, 
    .bot-message h4, 
    .bot-message h5, 
    .bot-message h6 {{
        font-size: 16px !important;
        font-weight: 600 !important;
        margin: 8px 0 4px 0 !important;
        line-height: 1.4 !important;
        color: {theme_vars['chat_bot_text']} !important;
    }}
    
    .bot-message p {{
        margin: 4px 0 !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }}
    
    .bot-message ul, .bot-message ol {{
        margin: 8px 0 !important;
        padding-left: 20px !important;
    }}
    
    .bot-message li {{
        margin: 2px 0 !important;
        font-size: 14px !important;
    }}
    
    .bot-message strong {{
        font-weight: 600 !important;
        font-size: 14px !important;
    }}
    
    .bot-message code {{
        background: rgba(255,255,255,0.1);
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 13px;
    }}
    
    /* Ensure no large headers in chat */
    .stChatMessage h1,
    .stChatMessage h2,
    .stChatMessage h3 {{
        font-size: 16px !important;
        font-weight: 600 !important;
        margin: 8px 0 4px 0 !important;
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
        border-radius: 8px;
        border: 1px solid {theme_vars['input_border']};
        padding: 0.75rem 1rem;
        font-size: 0.95rem;
        background-color: {theme_vars['input_bg']} !important;
        color: {theme_vars['text_color']} !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }}
        color: {theme_vars['text_color']} !important;
    }}
    
    /* Prevent input from going grey/disabled */
    .stTextInput > div > div > input:disabled,
    .stTextInput > div > div > input[disabled] {{
        background-color: {theme_vars['input_bg']} !important;
        color: {theme_vars['text_color']} !important;
        opacity: 1 !important;
    }}
    
    /* Override any grey state during processing */
    .stTextInput > div > div > input {{
        background-color: {theme_vars['input_bg']} !important;
        color: {theme_vars['text_color']} !important;
    }}
        background-color: {theme_vars['input_bg']};
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div > select {{
        background-color: {theme_vars['input_bg']};
        color: {theme_vars['text_color']};
        border: 1px solid {theme_vars['input_border']};
        border-radius: 8px;
        padding: 0.5rem;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: {theme_vars['primary_color']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.5rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }}
    
    .stButton > button:hover {{
        background: {theme_vars['button_hover']};
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }}
    
    /* Send button specific styling - Match username styling */
    .stForm .stButton > button,
    form .stButton > button,
    div[data-testid="stForm"] .stButton > button,
    .stButton > button[kind="formSubmit"] {{
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
        color: #1f2937 !important;
        border: 1px solid #7dd3fc !important;
        border-radius: 10px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        box-shadow: 0 2px 6px rgba(125, 211, 252, 0.2) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }}
    
    .stForm .stButton > button:hover,
    form .stButton > button:hover,
    div[data-testid="stForm"] .stButton > button:hover,
    .stButton > button[kind="formSubmit"]:hover {{
        background: linear-gradient(135deg, #bae6fd 0%, #93c5fd 100%) !important;
        border-color: #60a5fa !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(96, 165, 250, 0.3) !important;
        color: #1f2937 !important;
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
        border-radius: 8px;
    }}
    
    /* Improve text area styling */
    .stTextArea > div > div > textarea {{
        border-radius: 8px;
        border: 1px solid {theme_vars['input_border']};
        background-color: {theme_vars['input_bg']};
        color: {theme_vars['text_color']};
        font-size: 0.95rem;
    }}
    
    /* File uploader styling */
    .stFileUploader > div > div {{
        border: 1px dashed {theme_vars['input_border']};
        border-radius: 8px;
        background-color: {theme_vars['input_bg']};
    }}
    
    /* Metric styling */
    .metric-container {{
        background: {theme_vars['card_bg']};
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid {theme_vars['border_color']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    
    /* DataFrame styling */
    .stDataFrame {{
        border: 1px solid {theme_vars['border_color']};
        border-radius: 8px;
        overflow: hidden;
    }}
    
    /* Info, success, warning, error messages */
    .stAlert {{
        border-radius: 8px;
        border-left-width: 4px;
    }}
    
    .streamlit-expanderContent {{
        background-color: {theme_vars['card_bg']};
        color: {theme_vars['text_color']};
        border: 1px solid {theme_vars['border_color']};
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
    
    /* Light blue styling for specific text elements */
    .sidebar .stMarkdown p strong,
    .sidebar .stMarkdown li strong,
    [data-testid="stSidebar"] .stMarkdown p strong,
    [data-testid="stSidebar"] .stMarkdown li strong {{
        color: {theme_vars['header_text']} !important;
    }}
    
    /* Dropdown styling */
    .stSelectbox label,
    [data-testid="stSelectbox"] label,
    .stSelectbox > div > div > div {{
        color: {theme_vars['header_text']} !important;
    }}
    
    /* Organization and Role styling */
    [data-testid="stSidebar"] .stMarkdown li {{
        color: {theme_vars['header_text']} !important;
    }}
    
    /* Try these example queries dropdown */
    div[data-baseweb="select"] > div {{
        color: #333333 !important;
        background-color: #f8fafc !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
    }}
    
    /* Selectbox dropdown background */
    [data-testid="stSelectbox"] > div > div,
    .stSelectbox > div > div,
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div > div {{
        background-color: #f8fafc !important;
        color: #333333 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
    }}
    
    /* Selectbox button/dropdown toggle */
    [data-testid="stSelectbox"] button,
    div[data-baseweb="select"] button {{
        background-color: #f8fafc !important;
        color: #333333 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
    }}
    
    /* Dropdown menu options (when expanded) - the black area you see */
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] ul,
    div[data-baseweb="menu"] li,
    div[data-baseweb="popover"] div[data-baseweb="menu"],
    [data-baseweb="menu"] ul[role="listbox"],
    [data-baseweb="menu"] li[role="option"],
    div[data-baseweb="popover"] {{
        background-color: #f8fafc !important;
        color: #333333 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }}
    
    /* Selectbox hover states */
    [data-baseweb="menu"] li[role="option"]:hover,
    div[data-baseweb="menu"] li:hover {{
        background-color: #e0f2fe !important;
        color: #333333 !important;
    }}
    
    /* Reduce spacing between selectbox and form */
    [data-testid="stSelectbox"] {{
        margin-bottom: 0.5rem !important;
    }}
    
    /* Reduce spacing around form elements */
    [data-testid="stForm"] {{
        margin-top: 0.5rem !important;
    }}
    
    /* Reduce spacing in main content area */
    .block-container .element-container {{
        margin-bottom: 0.5rem !important;
    }}
    
    /* Ultra-compact sidebar spacing */
    section[data-testid="stSidebar"] .element-container {{
        margin-bottom: 0.1rem !important;
        margin-top: 0.1rem !important;
    }}
    
    /* Minimize spacing between sidebar sections */
    section[data-testid="stSidebar"] .stMarkdown {{
        margin-bottom: 0.2rem !important;
        margin-top: 0.2rem !important;
    }}
    
    /* Ultra-tight spacing around buttons in sidebar */
    section[data-testid="stSidebar"] .stButton {{
        margin-bottom: 0.15rem !important;
        margin-top: 0.15rem !important;
    }}
    
    /* Minimize expander spacing */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {{
        margin-bottom: 0.1rem !important;
        margin-top: 0.1rem !important;
        padding: 0.4rem 0.75rem !important;
    }}
    
    /* Ultra-compact dividers in sidebar */
    section[data-testid="stSidebar"] hr {{
        margin: 0.2rem 0 !important;
    }}
    
    /* Minimize spacing in sidebar headers */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {{
        margin-bottom: 0.15rem !important;
        margin-top: 0.2rem !important;
        line-height: 1.2 !important;
    }}
    
    /* Compact sidebar buttons */
    section[data-testid="stSidebar"] .stButton button {{
        padding: 0.4rem 0.75rem !important;
        font-size: 0.85rem !important;
    }}
    
    /* Reduce expander content padding */
    section[data-testid="stSidebar"] .streamlit-expanderContent {{
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }}
    
    /* Minimize caption spacing */
    section[data-testid="stSidebar"] .stCaptionContainer {{
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }}
    
    /* Minimize overall sidebar padding */
    section[data-testid="stSidebar"] > div {{
        padding-top: 0.1rem !important;
        padding-bottom: 0.5rem !important;
    }}
    
    /* Remove top padding from sidebar content */
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    
    /* Target sidebar wrapper for minimal spacing */
    section[data-testid="stSidebar"] > div > div {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    
    /* Remove spacing from first element in sidebar */
    section[data-testid="stSidebar"] > div > div > div:first-child {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}
    
    /* Ultra-compact conversation items */
    section[data-testid="stSidebar"] .stColumns {{
        gap: 0.1rem !important;
    }}
    
    /* Minimize text spacing in sidebar */
    section[data-testid="stSidebar"] p {{
        margin-bottom: 0.1rem !important;
        margin-top: 0.1rem !important;
        line-height: 1.3 !important;
    }}
    
    /* Compact write/caption text */
    section[data-testid="stSidebar"] .stWrite,
    section[data-testid="stSidebar"] .stCaption {{
        margin-bottom: 0.1rem !important;
        margin-top: 0.1rem !important;
    }}
    
    /* Make sidebar content ultra-tight */
    section[data-testid="stSidebar"] [data-testid="element-container"] {{
        margin: 0.05rem 0 !important;
    }}
</style>
"""

st.markdown(get_theme_css(), unsafe_allow_html=True)

# Add aggressive CSS to override any remaining dark elements
st.markdown("""
<style>
    /* MAXIMUM AGGRESSIVE CSS - Override ALL possible dark elements */
    
    /* Target every possible dropdown/menu container with maximum specificity */
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] *,
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    .stApp div[data-baseweb="menu"],
    .stApp div[data-baseweb="menu"] *,
    .stApp div[data-baseweb="popover"],
    .stApp div[data-baseweb="popover"] *,
    [data-testid="stSelectbox"] div[data-baseweb="menu"],
    [data-testid="stSelectbox"] div[data-baseweb="menu"] *,
    [data-testid="stSelectbox"] div[data-baseweb="popover"],
    [data-testid="stSelectbox"] div[data-baseweb="popover"] *,
    .stApp [data-testid="stSelectbox"] div[data-baseweb="menu"],
    .stApp [data-testid="stSelectbox"] div[data-baseweb="menu"] *,
    .stApp [data-testid="stSelectbox"] div[data-baseweb="popover"],
    .stApp [data-testid="stSelectbox"] div[data-baseweb="popover"] * {
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        color: #333333 !important;
        border-color: #d1d5db !important;
    }
    
    /* Target all list elements in dropdowns with maximum specificity */
    ul[role="listbox"],
    ul[role="listbox"] *,
    li[role="option"],
    li[role="option"] *,
    .stApp ul[role="listbox"],
    .stApp ul[role="listbox"] *,
    .stApp li[role="option"],
    .stApp li[role="option"] *,
    div[data-baseweb="menu"] ul,
    div[data-baseweb="menu"] ul *,
    div[data-baseweb="menu"] li,
    div[data-baseweb="menu"] li *,
    .stApp div[data-baseweb="menu"] ul,
    .stApp div[data-baseweb="menu"] ul *,
    .stApp div[data-baseweb="menu"] li,
    .stApp div[data-baseweb="menu"] li * {
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        color: #333333 !important;
    }
    
    /* Override any element with dark inline styles */
    .stApp *[style*="background-color: rgb(38, 39, 48)"],
    .stApp *[style*="background-color: #262730"],
    .stApp *[style*="background-color: rgb(14, 17, 23)"],
    .stApp *[style*="background-color: #0e1117"],
    .stApp *[style*="background: rgb(38, 39, 48)"],
    .stApp *[style*="background: #262730"],
    .stApp *[style*="background: rgb(14, 17, 23)"],
    .stApp *[style*="background: #0e1117"] {
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        color: #333333 !important;
    }
    
    /* Force all selectbox related elements to be light with maximum specificity */
    .stSelectbox,
    .stSelectbox *,
    [data-testid="stSelectbox"],
    [data-testid="stSelectbox"] *,
    .stApp .stSelectbox,
    .stApp .stSelectbox *,
    .stApp [data-testid="stSelectbox"],
    .stApp [data-testid="stSelectbox"] * {
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        color: #333333 !important;
    }
    
    /* Nuclear option - override ANY element that might be dark */
    .stApp * {
        background-color: #f8fafc !important;
        color: #333333 !important;
    }
    
    /* But keep specific light elements as they should be */
    .stApp .main-container,
    .stApp .main-title,
    .stApp .sidebar .element-container {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
    }
    
    /* Hide the troublesome small blue box element */
    span.st-emotion-cache-gi0tri.e1hznt4w3,
    .st-emotion-cache-gi0tri,
    span[class*="st-emotion-cache-gi0tri"],
    span[class*="e1hznt4w3"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }
    
    /* Hide any streamlit generated icons or elements in header area */
    .main-title span,
    .main-container span[class*="st-emotion"],
    h1 span[class*="st-emotion"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Add JavaScript to force sidebar expansion
st.markdown("""
<script>
// Force sidebar to be expanded
function forceSidebarExpansion() {
    // Try multiple methods to ensure sidebar is visible
    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.style.display = 'block';
        sidebar.style.visibility = 'visible';
        sidebar.style.transform = 'translateX(0px)';
        // Allow sidebar to be resizable - remove fixed width constraints
        sidebar.style.minWidth = '18rem';
        sidebar.style.width = 'auto';
    }
    
    // Don't hide the collapse button - allow sidebar to be collapsible
    // This enables proper sidebar functionality including resizing
    const collapseBtn = document.querySelector('button[data-testid="collapsedControl"]');
    if (collapseBtn) {
        collapseBtn.style.display = 'block'; // Keep it visible for proper functionality
    }
    
    // Set sidebar state in localStorage to expanded
    try {
        localStorage.setItem('stSidebarState', 'expanded');
        // Also try other possible keys
        localStorage.setItem('stSidebarCollapsed', 'false');
    } catch (e) {
        console.log('Could not set localStorage');
    }
}

// Run immediately and on DOM changes
forceSidebarExpansion();
setTimeout(forceSidebarExpansion, 100);
setTimeout(forceSidebarExpansion, 500);
setTimeout(forceSidebarExpansion, 1000);

// Observe for DOM changes
const observer = new MutationObserver(forceSidebarExpansion);
observer.observe(document.body, { childList: true, subtree: true });

// Force text colors to be visible
function forceTextColors() {
    const style = document.createElement('style');
    style.innerHTML = `
        /* Override all Streamlit default white text with dark text */
        .stApp *, 
        .stApp div,
        .stApp span,
        .stApp p,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp label,
        .element-container *,
        .block-container *,
        section[data-testid="stSidebar"] *,
        .css-1d391kg *,
        .stSidebar *,
        .sidebar-content *,
        [data-testid="stSidebar"] *,
        .stMarkdown *,
        .stText *,
        div[data-testid="stMarkdownContainer"] *,
        .css-1cpxqw2 *,
        .css-1y4p8pa *,
        .css-16huue1 * {
            color: #1f2937 !important;
        }
        
        /* Keep white text only for elements with dark backgrounds */
        .user-message *,
        .stButton > button,
        .css-1cpxqw2 button * {
            color: white !important;
        }
    `;
    document.head.appendChild(style);
}

// Apply text color fixes
forceTextColors();
setTimeout(forceTextColors, 100);
setTimeout(forceTextColors, 500);

// Additional form styling
const formStyle = document.createElement('style');
formStyle.innerHTML = `
    /* Form elements specific styling */
    .stTextInput > label, .stTextInput > div > label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    
    .stTextInput input {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stTextInput input::placeholder {
        color: #6b7280 !important;
    }
    
    .stTextInput input:focus {
        border-color: #9ca3af !important;
        box-shadow: 0 0 0 3px rgba(156, 163, 175, 0.2) !important;
        background-color: #ffffff !important;
        outline: none !important;
    }
    
    /* Button styling for visibility */
    .stButton > button {
        color: #ffffff !important;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
    }
    
    /* Help text */
    .stTextInput .help {
        color: #6b7280 !important;
    }
    
    /* Markdown headers and text */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #1f2937 !important;
    }
    
    .stMarkdown p {
        color: #1f2937 !important;
    }
    
    /* Form elements - more aggressive overrides */
    .stTextInput label, .stTextInput > label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    
    .stTextInput > div > div > div > input {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stTextInput input::placeholder {
        color: #6b7280 !important;
    }
    
    /* Form submit button - light theme */
    .stFormSubmitButton button {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
        font-weight: 600 !important;
    }
    
    .stFormSubmitButton button:hover {
        background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%) !important;
        border: 1px solid #9ca3af !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* All text elements */
    .stApp * {
        color: #1f2937 !important;
    }
    
    /* Specific form container */
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
    }
    
    [data-testid="stForm"] label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    
    /* Text input styling */
    [data-testid="textInput"] input {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }

    /* Streamlit form labels and text */


    /* Text input labels */
    .stTextInput > label,
    [data-testid="stTextInput"] > label,
    .stTextInput label,
    [data-testid="stTextInput"] label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }

    /* Form container text */
    [data-testid="stForm"] label,
    [data-testid="stForm"] p,
    [data-testid="stForm"] div,
    .stForm label,
    .stForm p,
    .stForm div {
        color: #1f2937 !important;
    }

    /* All form text elements */
    form label,
    form p,
    form div,
    .element-container label,
    .element-container p {
        color: #1f2937 !important;
    }

    /* Input help text */
    .help-text,
    [data-testid="stTextInput"] .help-text,
    small {
        color: #6b7280 !important;
    }

    /* Force all text to be dark and visible */
    * {
        color: #1f2937 !important;
    }
    
    /* Override markdown text specifically */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] strong,
    .stMarkdown p,
    .stMarkdown strong {
        color: #1f2937 !important;
    }
    
    /* Form submit button with light styling */
    [data-testid="stFormSubmitButton"] button,
    .stButton button {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        color: #374151 !important;
        border: 2px solid #d1d5db !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        transition: none !important;
    }
    
    [data-testid="stFormSubmitButton"] button:hover,
    .stButton button:hover {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        color: #374151 !important;
        border: 2px solid #d1d5db !important;
        transform: none !important;
    }
    
    /* Additional specific styling for Initialize nQuiry button */
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        color: #1f2937 !important;
        border: 2px solid #d1d5db !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%) !important;
        border-color: #9ca3af !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    /* Ultra-specific button styling to override Streamlit defaults */
    .stApp [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        color: #374151 !important;
        border: 2px solid #d1d5db !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stApp [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        border: 2px solid #d1d5db !important;
        color: #374151 !important;
        transform: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stApp [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:active {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        transform: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Even more specific targeting */
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%) !important;
        color: #374151 !important;
        border: 2px solid #d1d5db !important;
    }
`;
document.head.appendChild(formStyle);
</script>
""", unsafe_allow_html=True)

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

    # Add ticket form state variables
    if 'show_ticket_form' not in st.session_state:
        st.session_state.show_ticket_form = False
    if 'ticket_query' not in st.session_state:
        st.session_state.ticket_query = ""


def _format_timestamp_to_local(ts):
    """Format a stored UTC datetime to local time string HH:MM.

    Handles naive datetimes (assumed UTC) and timezone-aware datetimes.
    Falls back to str(ts) if formatting fails.
    """
    try:
        if not ts:
            return ""
        # If object has strftime, treat as datetime-like
        if hasattr(ts, 'strftime'):
            # If naive, assume UTC
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            # Convert to local timezone
            local_ts = ts.astimezone()
            return local_ts.strftime("%H:%M")
        return str(ts)
    except Exception:
        try:
            return str(ts)
        except Exception:
            return ""

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
                'timestamp': _format_timestamp_to_local(msg.get('timestamp'))
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
                'timestamp': _format_timestamp_to_local(msg.get('timestamp'))
            }
            chat_history.append(converted_msg)
        
        # Ensure the most recent messages are shown first (newest at top)
        chat_history = list(reversed(chat_history))
        st.session_state.chat_history = chat_history
        return True
    except Exception as e:
        print(f"Error loading chat history: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_conversation_thread(user_id, conversation):
    """Load an entire conversation thread into the chat history"""
    try:
        # Clear current chat history
        st.session_state.chat_history = []
        
        # Load all messages from the conversation thread
        for msg in conversation['messages']:
            # Convert MongoDB message format to Streamlit chat format
            message_type = 'user' if msg['role'] == 'user' else 'bot'
            timestamp = _format_timestamp_to_local(msg.get('timestamp'))
            
            st.session_state.chat_history.append({
                'type': message_type,
                'content': msg['message'],
                'timestamp': timestamp
            })
        
        return True
    except Exception as e:
        print(f"Error loading conversation thread: {e}")
        return False

def load_conversation_by_question(user_id, question):
    """Load the conversation that contains a specific question (legacy support)"""
    try:
        # Use the processor's chat manager instead of creating a new one
        chat_manager = None
        if hasattr(st.session_state, 'nquiry_processor') and st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
            chat_manager = st.session_state.nquiry_processor.chat_history_manager
        else:
            # Fallback to session state chat manager
            if not hasattr(st.session_state, 'chat_manager') or not st.session_state.chat_manager:
                st.session_state.chat_manager = ChatHistoryManager()
            chat_manager = st.session_state.chat_manager
        
        # Get full chat history from MongoDB
        mongo_history = chat_manager.get_history(user_id)
        
        # Find the conversation that contains this question
        conversation_messages = []
        found_question = False
        
        for i, msg in enumerate(mongo_history):
            if msg['role'] == 'user' and msg['message'].strip() == question.strip():
                found_question = True
                # Start collecting messages from this question
                conversation_messages = []
                
                # Add the question
                conversation_messages.append(msg)
                
                # Add all subsequent assistant responses for this question
                for j in range(i + 1, len(mongo_history)):
                    next_msg = mongo_history[j]
                    if next_msg['role'] == 'assistant':
                        conversation_messages.append(next_msg)
                    elif next_msg['role'] == 'user':
                        # Check if it's the same question (duplicate) - if so, skip it
                        if next_msg['message'].strip() == question.strip():
                            continue
                        else:
                            # Different user question - stop here
                            break
                break
        
        if found_question:
            # Convert to Streamlit format
            chat_history = []
            for msg in conversation_messages:
                msg_type = 'bot' if msg['role'] == 'assistant' else msg['role']
                content = msg['message']
                chat_history.append({
                    'type': msg_type,
                    'content': content,
                    'timestamp': _format_timestamp_to_local(msg.get('timestamp'))
                })
            # Keep chronological order: user question followed by assistant responses
            # (do not reverse here)
            
            st.session_state.chat_history = chat_history
            return True
        
        return False
    except Exception as e:
        print(f"Error loading conversation by question: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_past_conversations(user_id):
    """Get past conversations grouped into threads for sidebar display"""
    try:
        # Use the processor's chat manager instead of creating a new one
        chat_manager = None
        if hasattr(st.session_state, 'nquiry_processor') and st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
            chat_manager = st.session_state.nquiry_processor.chat_history_manager
        else:
            # Fallback to session state chat manager
            if not hasattr(st.session_state, 'chat_manager') or not st.session_state.chat_manager:
                st.session_state.chat_manager = ChatHistoryManager()
            chat_manager = st.session_state.chat_manager
        
        # Get full chat history from MongoDB
        mongo_history = chat_manager.get_history(user_id)
        
        # Group messages into conversation threads
        conversations = []
        current_conversation = []
        conversation_start_time = None
        
        for i, msg in enumerate(mongo_history):
            msg_time = msg.get('timestamp')
            
            # Start a new conversation if:
            # 1. This is the first message, OR
            # 2. This is a user message and we have a gap of more than 30 minutes from the last message
            if (len(current_conversation) == 0 or 
                (msg['role'] == 'user' and len(current_conversation) > 0 and 
                 _is_time_gap_significant(conversation_start_time, msg_time))):
                
                # Save the previous conversation if it exists
                if current_conversation:
                    # Use the first user message as the conversation title
                    first_user_msg = next((m for m in current_conversation if m['role'] == 'user'), None)
                    if first_user_msg:
                        conversations.append({
                            'title': first_user_msg['message'][:50] + "..." if len(first_user_msg['message']) > 50 else first_user_msg['message'],
                            'full_title': first_user_msg['message'],
                            'timestamp': _format_timestamp_to_local(conversation_start_time),
                            'messages': current_conversation.copy()
                        })
                
                # Start new conversation
                current_conversation = [msg]
                conversation_start_time = msg_time
            else:
                # Add to current conversation
                current_conversation.append(msg)
        
        # Don't forget the last conversation
        if current_conversation:
            first_user_msg = next((m for m in current_conversation if m['role'] == 'user'), None)
            if first_user_msg:
                conversations.append({
                    'title': first_user_msg['message'][:50] + "..." if len(first_user_msg['message']) > 50 else first_user_msg['message'],
                    'full_title': first_user_msg['message'],
                    'timestamp': _format_timestamp_to_local(conversation_start_time),
                    'messages': current_conversation.copy()
                })
        
        return conversations[-5:]  # Return last 5 conversations
    except Exception as e:
        print(f"Error getting past conversations: {e}")
        return []

def _is_time_gap_significant(time1, time2, gap_minutes=30):
    """Check if there's a significant time gap between two timestamps"""
    try:
        if not time1 or not time2:
            return True
        
        from datetime import datetime, timedelta
        
        # Handle both datetime objects and strings
        if isinstance(time1, str):
            time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
        if isinstance(time2, str):
            time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
        
        time_diff = abs((time2 - time1).total_seconds() / 60)  # in minutes
        return time_diff > gap_minutes
    except Exception as e:
        print(f"Error comparing timestamps: {e}")
        return True  # Default to starting new conversation on error
    except Exception as e:
        print(f"Error getting past conversations: {e}")
        return []

def save_message_to_history(user_id, role, content):
    """Save a message to MongoDB"""
    try:
        # Use the processor's chat manager instead of creating a new one
        chat_manager = None
        if hasattr(st.session_state, 'nquiry_processor') and st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
            chat_manager = st.session_state.nquiry_processor.chat_history_manager
        else:
            # Fallback to session state chat manager
            if not hasattr(st.session_state, 'chat_manager') or not st.session_state.chat_manager:
                st.session_state.chat_manager = ChatHistoryManager()
            chat_manager = st.session_state.chat_manager
        
        # ChatHistoryManager expects 'message' parameter, not 'content'
        chat_manager.add_message(user_id, role, content)
        return True
    except Exception as e:
        print(f"Error saving message: {e}")
        return False

def detect_conversation_ending_response(user_input):
    """Detect if user wants to end the conversation (saying no to ticket creation)"""
    user_input_lower = user_input.lower().strip()
    
    # Check for negative responses
    negative_responses = [
        'no', 'nope', 'no thanks', 'no thank you', 'not now', 
        'not needed', 'not required', 'i\'m good', 'im good',
        'that\'s all', 'thats all', 'nothing else', 'no need',
        'no ticket', 'don\'t need', 'dont need', 'sufficient',
        'enough', 'that helps', 'thanks', 'thank you'
    ]
    
    # Also check if the last bot message was asking about ticket creation
    if len(st.session_state.chat_history) > 0:
        last_bot_message = None
        for msg in reversed(st.session_state.chat_history):
            if msg.get('type') == 'bot':
                last_bot_message = msg.get('content', '').lower()
                break
        
        if last_bot_message and 'create a support ticket' in last_bot_message:
            # If the bot asked about ticket creation and user gave a negative response
            return any(response in user_input_lower for response in negative_responses)
    
    return False

def generate_thank_you_message():
    """Generate a thank you message to end the conversation gracefully"""
    customer_info = st.session_state.customer_info or {}
    org = customer_info.get('organization', 'your organization')
    
    return f"""
🙏 **Thank you for using Nquiry!**

I'm glad I could help you find the information you needed. If you have any other questions in the future, feel free to ask.

Have a great day!
    """.strip()

def is_direct_ticket_request(query):
    """Check if the user is directly requesting to create a ticket"""
    query_lower = query.lower().strip()
    ticket_keywords = [
        'create a ticket', 'create ticket', 'make a ticket', 'make ticket',
        'open a ticket', 'open ticket', 'submit a ticket', 'submit ticket',
        'file a ticket', 'file ticket', 'raise a ticket', 'raise ticket',
        'log a ticket', 'log ticket', 'create support ticket', 'ticket for'
    ]
    return any(keyword in query_lower for keyword in ticket_keywords)

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
            return issue
    
    # If no pattern matches, return the original query
    return query

def generate_chat_transcript():
    """Generate a formatted chat transcript for download"""
    if not st.session_state.chat_history:
        return ""
    
    from datetime import datetime
    customer_info = st.session_state.customer_info or {}
    
    # Build the transcript
    transcript_lines = []
    transcript_lines.append("NQUIRY CHAT TRANSCRIPT")
    transcript_lines.append("=" * 50)
    transcript_lines.append("")
    transcript_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    transcript_lines.append(f"Customer: {customer_info.get('organization', 'Unknown')} ({customer_info.get('email', 'Unknown')})")
    transcript_lines.append(f"Session Messages: {len(st.session_state.chat_history)}")
    transcript_lines.append("")
    transcript_lines.append("CONVERSATION LOG:")
    transcript_lines.append("-" * 30)
    transcript_lines.append("")
    
    # Add each message
    for i, message in enumerate(st.session_state.chat_history, 1):
        msg_type = message.get('type', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        if msg_type == 'user':
            transcript_lines.append(f"[{timestamp}] 👤 USER:")
            transcript_lines.append(f"    {content}")
        elif msg_type == 'bot':
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
    
    transcript_lines.append("=" * 50)
    transcript_lines.append("End of Transcript")
    transcript_lines.append("")
    transcript_lines.append("Generated by Nquiry - Intelligent Query Processing System")
    
    return '\n'.join(transcript_lines)

def generate_jira_ticket_id(category):
    """Generate a JIRA-style ticket ID with product category prefix and random number"""
    import random
    
    # Get product category prefix
    if category:
        # Use the category directly as prefix (NOC, COPS, MNHT, etc.)
        prefix = category.upper().strip()
    else:
        prefix = 'SUP'  # Default support prefix
    
    # Generate random 5-digit number
    random_number = random.randint(10000, 99999)
    
    return f"{prefix}-{random_number}"

def display_header():
    """Display the main header with user info"""
    customer_info = st.session_state.customer_info or {}
    
    # Simple user menu in top right if logged in
    if customer_info:
        col1, col2, col3 = st.columns([5, 2, 3])
        
        with col3:
            email = customer_info.get('email', 'Unknown')
            user_name = email.split('@')[0] if email != 'Unknown' else 'User'
            
            # Create dropdown with username and logout option - make it wider
            user_action = st.selectbox(
                "User Menu",
                options=[f"👤 {user_name}", "🚪 Logout"],
                index=0,
                key="user_dropdown",
                label_visibility="collapsed",
                help=f"Logged in as: {email}"
            )
            
            # Handle logout action
            if user_action == "🚪 Logout":
                # Clear all session state to logout user
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                # Reinitialize session state
                initialize_session_state()
                
                # Force rerun to show login page
                st.rerun()

def display_system_status():
    """Display system status in sidebar"""
    
    # Add elegant Nquiry title at the top of sidebar
    st.sidebar.markdown("""
    <h1 style="
        color: #1f2937;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0 0 2rem 0;
        padding: 0;
        text-align: left;
        letter-spacing: -0.5px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    ">Nquiry</h1>
    """, unsafe_allow_html=True)
    
    if st.session_state.nquiry_processor:
        try:
            # Get system status from the processor
            processor = st.session_state.nquiry_processor
            customer_info = st.session_state.customer_info or {}
            
            # Display customer info - simplified format
            org = customer_info.get('organization', 'Unknown')
            
            st.sidebar.markdown(f"""
            **Customer:** {org}
            """, unsafe_allow_html=True)
            
            # Recent Chat History Dropdown
            
            # Get user ID for chat history
            user_id = customer_info.get('email', 'demo_user') if customer_info else 'demo_user'
            
            # Get past conversations for sidebar
            past_conversations = get_past_conversations(user_id)
            
            if past_conversations:
                with st.sidebar.expander(f"Recent Conversations ({len(past_conversations)})", expanded=False):
                            # Show most recent first
                            for idx, conv in enumerate(reversed(past_conversations)):
                                # Use a proper timestamp and truncated title
                                timestamp = conv.get('timestamp', '')
                                title = conv.get('title', 'Untitled Conversation')
                                full_title = conv.get('full_title', title)
                                
                                # Show conversation stats
                                message_count = len(conv.get('messages', []))
                                user_msgs = len([m for m in conv.get('messages', []) if m['role'] == 'user'])
                                bot_msgs = len([m for m in conv.get('messages', []) if m['role'] == 'assistant'])

                                cols = st.columns([6, 2])
                                with cols[0]:
                                    if st.button(
                                        f"💬 {title}",
                                        key=f"conv_load_{idx}_{timestamp}",
                                        help=f"Load conversation thread ({user_msgs} questions, {bot_msgs} responses)\nStarted: {timestamp}",
                                        use_container_width=True
                                    ):
                                        if load_conversation_thread(user_id, conv):
                                            st.success(f"✅ Loaded conversation thread: {title}")
                                            st.rerun()
                                        else:
                                            st.error("❌ Could not load conversation thread")

                                with cols[1]:
                                    # Delete button for conversation
                                    if st.button(
                                        "🗑️ Delete",
                                        key=f"conv_delete_{idx}_{timestamp}",
                                        help=f"Delete this conversation thread",
                                        use_container_width=True
                                    ):
                                        # Call ChatHistoryManager to delete the conversation by question
                                        try:
                                            # Use the same chat manager as other functions
                                            chat_manager = None
                                            if hasattr(st.session_state, 'nquiry_processor') and st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
                                                chat_manager = st.session_state.nquiry_processor.chat_history_manager
                                            else:
                                                # Fallback to session state chat manager
                                                if not hasattr(st.session_state, 'chat_manager') or not st.session_state.chat_manager:
                                                    st.session_state.chat_manager = ChatHistoryManager()
                                                chat_manager = st.session_state.chat_manager
                                            
                                            deleted = chat_manager.delete_conversation_by_question(user_id, full_title)
                                            if deleted:
                                                st.success("🗑️ Conversation thread deleted")
                                            else:
                                                st.warning("No matching conversation found or nothing deleted")
                                        except Exception as e:
                                            st.error(f"Failed to delete conversation: {e}")
                                        st.rerun()

                                st.caption(f"⏰ {timestamp} • {message_count} messages")
                                st.markdown("<div style='border-bottom: 1px solid #e5e7eb; margin: 0.2rem 0;'></div>", unsafe_allow_html=True)
            else:
                with st.sidebar.expander("Recent Conversations", expanded=False):
                    st.write("No past conversations found")
                    st.caption("Start a conversation to see history")
            
            st.sidebar.markdown("<div style='margin: 0.1rem 0;'></div>", unsafe_allow_html=True)
            
            # Recent Tickets Dropdown
            
            # Get customer organization from session state
            customer_info = st.session_state.customer_info or {}
            organization = customer_info.get('organization', 'Unknown')
            
            # Show organization-specific recent tickets from JIRA
            with st.sidebar.expander("Recent Support Tickets", expanded=False):
                if organization and organization != 'Unknown' and st.session_state.nquiry_processor:
                    try:
                        # Get recent tickets from JIRA for this organization
                        jira_tool = st.session_state.nquiry_processor.jira_tool
                        recent_tickets = jira_tool.get_recent_tickets_by_organization(organization, limit=5)
                        
                        if recent_tickets:
                            st.markdown(f"**Recent tickets for {organization}:**")
                            
                            for ticket in recent_tickets:
                                # Create a more compact display
                                st.markdown(f"**[{ticket['key']}]({ticket['link']})**")
                                st.caption(f"🏷️ {ticket['status']} | ⚡ {ticket['priority']} | 📝 {ticket['issue_type']}")
                                
                                # Truncate summary if too long
                                summary = ticket['summary']
                                if len(summary) > 60:
                                    summary = summary[:60] + "..."
                                st.text(summary)
                                
                                # Parse and format the updated date
                                try:
                                    from datetime import datetime
                                    updated_str = ticket['updated']
                                    if updated_str:
                                        # JIRA returns ISO format like "2024-09-26T10:30:00.000+0000"
                                        updated_dt = datetime.fromisoformat(updated_str.replace('Z', '+00:00').replace('.000+', '+'))
                                        formatted_date = updated_dt.strftime("%m/%d %H:%M")
                                        st.caption(f"📅 Updated: {formatted_date}")
                                except:
                                    # Fallback if date parsing fails
                                    st.caption(f"📅 Updated: {ticket['updated'][:10]}")
                                
                                st.markdown("---")
                        else:
                            st.write(f"No recent support tickets found for {organization} in JIRA")
                            st.caption("🔍 JIRA tickets for your organization will appear here")
                    except Exception as e:
                        st.error(f"Error loading recent tickets: {str(e)}")
                        st.caption("❌ Unable to connect to JIRA at this time")
                else:
                    st.write("Organization not identified or system not initialized")
                    st.caption("💡 Please ensure your customer email is properly configured")
                
            st.sidebar.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            
            # Start New Conversation Button
            if st.sidebar.button("🆕 Start New Conversation", use_container_width=True, type="primary"):
                # Clear current chat history to start fresh
                st.session_state.chat_history = []
                st.session_state.conversation_ended = False  # Reset conversation ended flag
                
                # Clear all input field values
                if 'query_input' in st.session_state:
                    del st.session_state['query_input']
                if 'follow_up_input' in st.session_state:
                    del st.session_state['follow_up_input']
                if 'last_processed_query' in st.session_state:
                    del st.session_state['last_processed_query']
                if 'last_followup_query' in st.session_state:
                    del st.session_state['last_followup_query']
                
                # Force input field reset by changing keys
                if 'input_key_counter' not in st.session_state:
                    st.session_state.input_key_counter = 0
                st.session_state.input_key_counter += 1
                
                st.success("✅ Started new conversation!")
                st.rerun()
                
        except Exception as e:
            st.sidebar.error(f"Info unavailable: {e}")
    else:
        st.sidebar.info("Please initialize system first")

def initialize_nquiry():
    """Initialize Nquiry processor"""
    if not st.session_state.initialized:
        try:
            with st.spinner("🚀 Initializing Nquiry" \
            " system..."):
                # Create a placeholder for the email input since we can't use input() in Streamlit
                # We'll handle this differently in the Streamlit app
                st.session_state.nquiry_processor = "placeholder"  # Will be created when customer email is provided
                st.session_state.initialized = True
                st.success("✅ Nquiry system ready!")
        except Exception as e:
            st.error(f"❌ Failed to initialize Nquiry: {e}")
            st.exception(e)

def create_nquiry_processor(customer_email):
    """Create nQuiry
      processor with customer email"""
    try:
        # Temporarily patch the input function to return our email
        import builtins
        original_input = builtins.input
        builtins.input = lambda prompt="": customer_email
        
        try:
            processor = IntelligentQueryProcessor(streamlit_mode=True)
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
                        background: #f8fafc;
                        color: #374151;
                        padding: 1rem 1.5rem;
                        border-radius: 18px 18px 18px 4px;
                        max-width: 70%;
                        border-left: 3px solid #3b82f6;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
                        border: 1px solid #e5e7eb;
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
        # Check if this is a direct ticket creation request
        if is_direct_ticket_request(query):
            # Extract the actual issue from the ticket creation request
            actual_issue = extract_issue_from_ticket_request(query)
            st.session_state.show_ticket_form = True
            st.session_state.ticket_query = actual_issue
            return f"🎫 **Creating Support Ticket**\n\nI'll help you create a support ticket for: {actual_issue}\n\nPlease fill out the ticket form below to complete your support request."
        
        with st.spinner("🔍 Processing your query..."):
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate processing stages
            progress_bar.progress(25)
            time.sleep(0.5)
            
            progress_bar.progress(50)
            time.sleep(0.5)
            
            progress_bar.progress(75)
            time.sleep(0.5)
            
            # Get chat history for context from session state
            history = st.session_state.get('chat_history', [])
            
            # Convert session state format to the format expected by processor
            formatted_history = []
            for msg in history:
                formatted_history.append({
                    'role': 'user' if msg['type'] == 'user' else 'assistant',
                    'content': msg['content'],
                    'message': msg['content'],  # Fallback field name
                    'type': msg['type']  # Keep original type field
                })
            
            # Actually process the query, passing history for context
            result = processor.process_query(user_id, query, history=formatted_history)
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Extract the actual response content from the result
            response_text = ""
            if isinstance(result, dict):
                # Check if ticket creation is ready
                if result.get('ticket_creation_ready'):
                    # Trigger interactive ticket creation
                    st.session_state.show_ticket_form = True
                    st.session_state.ticket_query = result.get('original_query', query)
                    response_text = result.get('formatted_response', result.get('response', 'Ready to create ticket'))
                # Check if ticket creation is completed
                elif ('ticket_created' in result and result['ticket_created']):
                    response_text = f"🎫 **Ticket Created Successfully**\n\n{result['ticket_created']}"
                elif ('formatted_response' in result and result['formatted_response'] and 
                      "would you like me to create a support ticket" in result['formatted_response'].lower()):
                    # Trigger interactive ticket creation (fallback detection)
                    st.session_state.show_ticket_form = True
                    st.session_state.ticket_query = query
                    response_text = result['formatted_response']
                elif 'response' in result and result['response']:
                    response_text = result['response']
                elif 'formatted_response' in result and result['formatted_response']:
                    response_text = result['formatted_response']
                else:
                    response_text = "❌ Sorry, I couldn't find a relevant response to your query."
            else:
                # If result is a string, return as-is
                response_text = result if result else "❌ Sorry, I couldn't process your query."
            
            # Audio feedback if enabled
            if VOICE_AVAILABLE and st.session_state.get('audio_enabled', False):
                try:
                    # Clean the response for speech (remove markdown and emojis)
                    clean_text = response_text
                    # Remove markdown formatting
                    import re
                    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)  # Bold
                    clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)      # Italic
                    clean_text = re.sub(r'#{1,6}\s?', '', clean_text)           # Headers
                    clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)        # Code
                    clean_text = re.sub(r'[🎯🏷️👤✅📂📄❌🎫🔊🔤🎤💡🔍]', '', clean_text)  # Emojis
                    
                    # Limit speech to first 200 characters for better experience
                    if len(clean_text) > 200:
                        clean_text = clean_text[:200] + "... Response truncated for audio."
                    
                    # Play audio in background thread to avoid blocking UI
                    import threading
                    audio_thread = threading.Thread(target=speak_response, args=(clean_text,))
                    audio_thread.daemon = True
                    audio_thread.start()
                    
                except Exception as audio_error:
                    st.warning(f"Audio playback failed: {audio_error}")
            
            return response_text
            
    except Exception as e:
        st.error(f"Error processing query: {e}")
        return f"❌ Sorry, I encountered an error: {str(e)}"

def display_ticket_creation_form():
    """Display interactive ticket creation form"""
    if not st.session_state.show_ticket_form:
        return
        
    st.markdown("---")
    st.markdown("### 🎫 Create Support Ticket")
    st.markdown("Since no relevant information was found, let's create a support ticket for your query.")
    
    with st.form("ticket_creation_form"):
        # Display original query
        st.markdown(f"**Original Query:** {st.session_state.ticket_query}")
        
        # Ticket fields
        col1, col2 = st.columns(2)
        
        with col1:
            # Priority
            priority = st.selectbox(
                "Priority", 
                ["Medium", "High", "Low", "Highest", "Lowest"],
                index=0,
                help="Select the priority level for this ticket"
            )
            
            # Area affected
            area = st.selectbox(
                "Area Affected",
                ["Other", "UI/UX", "Performance", "Integration", "Data", "Security"],
                index=0,
                help="Select the area most affected by this issue"
            )
            
        with col2:
            # Version
            version = st.text_input(
                "Version Affected", 
                value="latest",
                help="Enter the version where this issue occurs"
            )
            
            # Environment
            environment = st.selectbox(
                "Environment",
                ["production", "staging", "development", "testing"],
                index=0,
                help="Select the environment where this issue occurs"
            )
        
        # Description (auto-filled but editable)
        description = st.text_area(
            "Description",
            value=f"User Query: {st.session_state.ticket_query}\n\nNo relevant information was found in the knowledge base. Please investigate and provide assistance.",
            height=100,
            help="Modify the description if needed"
        )
        
        # Buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            create_ticket = st.form_submit_button("🎫 Create Ticket", type="primary")
            
        with col2:
            cancel_ticket = st.form_submit_button("❌ Cancel")
            
        # Handle form submission
        if create_ticket:
            try:
                # Get customer email from session state
                customer_email = st.session_state.customer_info.get('email', 'demo@example.com') if st.session_state.customer_info else 'demo@example.com'
                
                # Create ticket data
                from ticket_creator import TicketCreator
                ticket_creator = TicketCreator()
                
                # Prepare ticket data based on form inputs
                ticket_data = {
                    'original_query': st.session_state.ticket_query,
                    'description': description,
                    'priority': priority,
                    'area_affected': area.lower().replace('/', '_').replace(' ', '_'),
                    'version_affected': version,
                    'environment': environment
                }
                
                # Create the ticket
                result = ticket_creator.create_ticket_streamlit(st.session_state.ticket_query, customer_email, ticket_data)
                
                # Generate JIRA-style ticket ID first
                category = result.get('category', '')
                jira_ticket_id = generate_jira_ticket_id(category)
                
                # Display success message
                st.success("🎫 **Ticket Created Successfully!**")
                st.markdown(f"**Ticket ID:** {result.get('ticket_id', 'N/A')}")
                st.markdown(f"**JIRA Ticket:** {jira_ticket_id}")
                st.markdown(f"**Category:** {result.get('category', 'N/A')}")
                st.markdown(f"**Customer:** {result.get('customer', 'N/A')}")
                
                # Create detailed ticket document content
                ticket_document = []
                ticket_document.append("TICKET SIMULATION OUTPUT")
                ticket_document.append("========================")
                ticket_document.append("")
                ticket_document.append(f"Ticket ID: {result.get('ticket_id', 'N/A')}")
                ticket_document.append(f"JIRA Ticket: {jira_ticket_id}")
                ticket_document.append(f"Category: {result.get('category', 'N/A')}")
                ticket_document.append(f"Customer: {result.get('customer', 'N/A')}")
                ticket_document.append(f"Created: {result.get('created_date', 'N/A')}")
                ticket_document.append(f"Customer Email: {customer_email}")
                ticket_document.append(f"Original Query: {result.get('original_query', 'N/A')}")
                ticket_document.append("")
                
                ticket_document.append("TICKET DETAILS:")
                ticket_document.append("===============")
                
                # Add all ticket fields
                excluded_fields = {'ticket_id', 'category', 'customer', 'created_date', 'customer_email', 'original_query'}
                for field, value in result.items():
                    if field not in excluded_fields:
                        field_name = field.replace('_', ' ').title()
                        ticket_document.append(f"{field_name}: {value}")
                
                ticket_document.append("")
                ticket_document.append("=" * 60)
                
                # Store ticket content in session state for download
                ticket_content = "\n".join(ticket_document)
                st.session_state.ticket_content = ticket_content
                st.session_state.ticket_filename = f"{result.get('ticket_id', 'ticket')}.txt"
                
                # Enhanced success message with both ticket IDs (using already generated jira_ticket_id)
                ticket_response = f"""🎫 **Ticket Created Successfully!**

**Ticket ID:** {result.get('ticket_id', 'N/A')}
**JIRA Ticket:** {jira_ticket_id}
**Category:** {result.get('category', 'N/A')}
**Customer:** {result.get('customer', 'N/A')}

✅ Your support ticket has been created and will be processed by our support team.
📄 Complete ticket details have been generated."""
                
                timestamp = datetime.now().strftime("%H:%M")
                st.session_state.chat_history.append({
                    'type': 'bot',
                    'content': ticket_response,
                    'timestamp': timestamp
                })
                
                # Save to history
                user_id = customer_email
                if st.session_state.chat_manager:
                    st.session_state.chat_manager.add_message(user_id, 'assistant', ticket_response)
                
                # Reset form state
                st.session_state.show_ticket_form = False
                st.session_state.ticket_query = ""
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error creating ticket: {str(e)}")
        
        elif cancel_ticket:
            # Reset form state
            st.session_state.show_ticket_form = False
            st.session_state.ticket_query = ""
            st.rerun()
    
    # Add download button outside the form if ticket content is available
    if hasattr(st.session_state, 'ticket_content') and st.session_state.ticket_content:
        st.download_button(
            label="📄 Download Complete Ticket Details",
            data=st.session_state.ticket_content,
            file_name=st.session_state.ticket_filename,
            mime='text/plain',
            use_container_width=True,
            key="download_ticket"
        )
        # Clear the content after download is available
        if st.button("✅ Clear Download", use_container_width=True):
            st.session_state.ticket_content = None
            st.session_state.ticket_filename = None
            st.rerun()

def main():
    """Main Streamlit app"""
    initialize_session_state()
    display_header()
    
    # Force sidebar to be visible with JavaScript
    st.markdown("""
    <script>
    setTimeout(function() {
        // Find sidebar and force it to be visible
        var sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
            sidebar.style.transform = 'translateX(0px)';
            sidebar.style.left = '0px';
            sidebar.style.width = '280px';
            sidebar.style.minWidth = '280px';
            sidebar.style.position = 'relative';
            sidebar.style.backgroundColor = '#DCDCDC';
            sidebar.style.zIndex = '999999';
            sidebar.setAttribute('aria-expanded', 'true');
        }
        
        // Hide any collapse buttons
        var collapseButtons = document.querySelectorAll('button[data-testid="collapsedControl"], .css-1dp5vir, button[aria-label*="collapse"]');
        collapseButtons.forEach(function(btn) {
            btn.style.display = 'none';
        });
        
        // Force main content to leave space
        var mainContent = document.querySelector('.main .block-container');
        if (mainContent) {
            mainContent.style.marginLeft = '300px';
        }
    }, 100);
    
    // Run again after 1 second to ensure it sticks
    setTimeout(function() {
        var sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
            sidebar.style.transform = 'translateX(0px)';
        }
    }, 1000);
    </script>
    """, unsafe_allow_html=True)
    
    # Sidebar
    display_system_status()
    
    # Customer email input (only if not initialized)
    if not st.session_state.nquiry_processor or st.session_state.nquiry_processor == "placeholder":
        st.markdown("### 🔐 Customer Authentication")
        
        st.markdown("**Please enter your email for customer identification:**", unsafe_allow_html=True)
        customer_email = st.text_input(
            "Customer Email",
            placeholder="your.email@company.com (Press Enter to initialize)",
            help="This is required for role-based access to JIRA and MindTouch. Press Enter after typing your email.",
            label_visibility="collapsed",
            key="customer_email_input"
        )
        
        # Auto-initialize when email is provided and user presses Enter
        if customer_email and customer_email.strip():
            # Check if this is a new email (to avoid re-initializing on every rerun)
            if "last_customer_email" not in st.session_state or st.session_state.last_customer_email != customer_email:
                with st.spinner("Initializing Nquiry with your credentials..."):
                    processor = create_nquiry_processor(customer_email)
                    if processor:
                        st.session_state.nquiry_processor = processor
                        st.session_state.last_customer_email = customer_email
                        st.success("✅ Nquiry initialized successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to initialize Nquiry")
        return
    
    # Main chat interface
    
    # Perplexity-style unified search interface
    st.markdown("""
    <style>
    .perplexity-container {
        max-width: 800px;
        margin: 2rem auto;
        padding: 0;
    }
    
    .help-text {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 400;
        color: #374151;
        margin-bottom: 2rem;
        line-height: 1.4;
    }
    
    .example-queries {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .example-title {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1rem;
        font-weight: 500;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the main container
    st.markdown('<div class="perplexity-container">', unsafe_allow_html=True)
    
    # Help text
    st.markdown('<div class="help-text">What can I help with?</div>', unsafe_allow_html=True)
    
    # Initialize session state for input focus
    if 'input_focused' not in st.session_state:
        st.session_state.input_focused = False
    if 'show_suggestions' not in st.session_state:
        st.session_state.show_suggestions = False
    
    # Example queries 
    example_queries = [
        "How do I reset my password?",
        "What are the system requirements?", 
        "How do I submit a bug report?",
        "Who should I contact for support?",
        "How do I update my profile?",
        "How to configure MFA settings?"
    ]
    
    # Audio feedback settings in top right
    col_spacer, col_audio = st.columns([4, 1])
    with col_audio:
        if VOICE_AVAILABLE:
            audio_enabled = st.checkbox("🔊 Audio", key="audio_enabled", help="Enable text-to-speech for bot responses")
    
    # Main input with microphone button
    col_input, col_mic = st.columns([9, 1])
    
    query = ""
    
    with col_input:
        # Initialize key counter if not exists
        if 'input_key_counter' not in st.session_state:
            st.session_state.input_key_counter = 0
            
        # Text input field with dynamic key
        query = st.text_input(
            "Search Query",
            placeholder="Ask anything or @mention a Space",
            key=f"search_input_{st.session_state.input_key_counter}",
            label_visibility="collapsed",
            help="Type your question here"
        )
    
    with col_mic:
        # Microphone button - always visible when voice is available
        if VOICE_AVAILABLE:
            if st.button("🎤", key="mic_button", help="Click to use voice input"):
                # Trigger voice recording
                st.session_state.use_voice = True
                st.rerun()
    
    # Handle voice input when microphone is clicked
    if VOICE_AVAILABLE and st.session_state.get('use_voice', False):
        # Reset voice flag
        st.session_state.use_voice = False
        
        # Show voice recording interface
        voice_query = create_voice_input_component()
        if voice_query:
            query = voice_query
    
    elif not VOICE_AVAILABLE:
        # Show fallback message when voice is not available but user tries to use mic
        if st.session_state.get('use_voice', False):
            st.error("❌ Voice input is not available. Please install required dependencies.")
            st.code("pip install speechrecognition pyaudio pyttsx3")
            st.session_state.use_voice = False
    
    # Show example queries only when input is empty (regardless of chat history)
    if not query or query.strip() == "":
        with st.expander("💡 Try asking:", expanded=True):
            st.markdown("**Choose from these example queries:**")
            
            # Show suggestions in a clean list
            for i, suggestion in enumerate(example_queries):
                if st.button(f"🔍 {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                    # Process the selected query immediately
                    user_id = st.session_state.customer_info.get('email', 'demo_user') if st.session_state.customer_info else 'demo_user'
                    
                    # Add to chat and process
                    timestamp = datetime.now().strftime("%H:%M")
                    st.session_state.chat_history.append({
                        'type': 'user',
                        'content': suggestion,
                        'timestamp': timestamp
                    })
                    
                    if st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
                        response = process_query(suggestion, st.session_state.nquiry_processor, user_id)
                        bot_timestamp = datetime.now().strftime("%H:%M")
                        st.session_state.chat_history.append({
                            'type': 'bot',
                            'content': response,
                            'timestamp': bot_timestamp
                        })
                        
                        # Force refresh of sidebar
                        if 'sidebar_refresh_trigger' not in st.session_state:
                            st.session_state.sidebar_refresh_trigger = 0
                        st.session_state.sidebar_refresh_trigger += 1
                        
                        # Increment input key counter to clear input fields
                        st.session_state.input_key_counter += 1
                    
                    st.rerun()
    
    # Handle manual query submission
    if query and query.strip():
        # Check if this is a new query (different from the last processed one)
        last_processed_query = st.session_state.get('last_processed_query', '')
        
        if query.strip() != last_processed_query and not st.session_state.get('processing_query', False):
            # Set processing flag and store the query
            st.session_state.processing_query = True
            st.session_state.last_processed_query = query.strip()
            
            # Process the manual query
            user_id = st.session_state.customer_info.get('email', 'demo_user') if st.session_state.customer_info else 'demo_user'
            
            # Add to chat and process
            timestamp = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append({
                'type': 'user',
                'content': query.strip(),
                'timestamp': timestamp
            })
            
            if st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
                
                # Check if this is a "no" response to ticket creation
                if detect_conversation_ending_response(query.strip()):
                    # End conversation gracefully
                    response = generate_thank_you_message()
                    st.session_state.conversation_ended = True
                else:
                    response = process_query(query.strip(), st.session_state.nquiry_processor, user_id)
                
                bot_timestamp = datetime.now().strftime("%H:%M")
                st.session_state.chat_history.append({
                    'type': 'bot',
                    'content': response,
                    'timestamp': bot_timestamp
                })
                
                # Force refresh of sidebar
                if 'sidebar_refresh_trigger' not in st.session_state:
                    st.session_state.sidebar_refresh_trigger = 0
                st.session_state.sidebar_refresh_trigger += 1
                
                # Increment input key counter to clear input fields
                st.session_state.input_key_counter += 1
            
            # Clear processing flag and rerun to clear input
            st.session_state.processing_query = False
            st.rerun()
    
    # Reset processing flag if no query
    elif not query or not query.strip():
        st.session_state.processing_query = False
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display chat history first
    display_chat_history()
    
    # Display ticket creation form immediately after chat history if needed
    display_ticket_creation_form()
    
    # Show download button for completed tickets after ticket form
    if hasattr(st.session_state, 'ticket_content') and st.session_state.ticket_content:
        st.markdown("---")
        st.markdown("### 📄 Downloads")
        
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.download_button(
                label="📄 Download Ticket Details",
                data=st.session_state.ticket_content,
                file_name=st.session_state.ticket_filename,
                mime='text/plain',
                use_container_width=True,
                key="download_ticket_main"
            )
        with col2:
            # Generate chat transcript (only available with ticket)
            chat_transcript = generate_chat_transcript()
            if chat_transcript:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                customer_info = st.session_state.customer_info or {}
                org = customer_info.get('organization', 'User')
                chat_filename = f"chat_transcript_{org}_{timestamp}.txt"
                
                st.download_button(
                    label="💬 Download Chat Transcript",
                    data=chat_transcript,
                    file_name=chat_filename,
                    mime='text/plain',
                    use_container_width=True,
                    key="download_chat_main"
                )
        with col3:
            if st.button("✅ Clear", use_container_width=True, key="clear_downloads_main"):
                st.session_state.ticket_content = None
                st.session_state.ticket_filename = None
                st.rerun()
    
    # Show follow-up input at the very bottom (after all other content)
    if len(st.session_state.chat_history) > 0 and not st.session_state.get('conversation_ended', False):
        st.markdown('<div style="margin-top: 2rem; border-top: 1px solid #e0e0e0; padding-top: 1rem;"></div>', unsafe_allow_html=True)
        
        # Follow-up input with microphone button
        col_followup, col_followup_mic = st.columns([10, 1])
        
        with col_followup:
            # Initialize key counter if not exists
            if 'input_key_counter' not in st.session_state:
                st.session_state.input_key_counter = 0
                
            follow_up_query = st.text_input(
                "Follow-up Question",
                placeholder="Ask another question...",
                key=f"follow_up_input_{st.session_state.input_key_counter}",
                label_visibility="collapsed",
                help="Type your follow-up question here"
            )
        
        with col_followup_mic:
            # Add spacing to align with input field
            st.markdown("<div style='padding-top: 8px;'></div>", unsafe_allow_html=True)
            # Microphone button for follow-up
            if VOICE_AVAILABLE:
                if st.button("🎤", key="followup_mic_button", help="Click to use voice input", use_container_width=True):
                    # Trigger voice recording for follow-up
                    st.session_state.use_followup_voice = True
                    st.rerun()
        
        # Handle voice input for follow-up when microphone is clicked
        if VOICE_AVAILABLE and st.session_state.get('use_followup_voice', False):
            # Reset voice flag
            st.session_state.use_followup_voice = False
            
            # Show voice recording interface
            followup_voice_query = create_voice_input_component()
            if followup_voice_query:
                follow_up_query = followup_voice_query
        
        # Handle follow-up query submission
        if follow_up_query and follow_up_query.strip():
            # Check if this is a new query
            last_followup_query = st.session_state.get('last_followup_query', '')
            
            if follow_up_query.strip() != last_followup_query:
                st.session_state.last_followup_query = follow_up_query.strip()
                
                # Process the follow-up query
                user_id = st.session_state.customer_info.get('email', 'demo_user') if st.session_state.customer_info else 'demo_user'
                
                # Add to chat and process
                timestamp = datetime.now().strftime("%H:%M")
                st.session_state.chat_history.append({
                    'type': 'user',
                    'content': follow_up_query.strip(),
                    'timestamp': timestamp
                })
                
                if st.session_state.nquiry_processor and st.session_state.nquiry_processor != "placeholder":
                    
                    # Check if this is a "no" response to ticket creation
                    if detect_conversation_ending_response(follow_up_query.strip()):
                        # End conversation gracefully
                        response = generate_thank_you_message()
                        st.session_state.conversation_ended = True
                    else:
                        response = process_query(follow_up_query.strip(), st.session_state.nquiry_processor, user_id)
                    
                    bot_timestamp = datetime.now().strftime("%H:%M")
                    st.session_state.chat_history.append({
                        'type': 'bot',
                        'content': response,
                        'timestamp': bot_timestamp
                    })
                    
                    # Force refresh of sidebar
                    if 'sidebar_refresh_trigger' not in st.session_state:
                        st.session_state.sidebar_refresh_trigger = 0
                    st.session_state.sidebar_refresh_trigger += 1
                    
                    # Increment input key counter to clear input fields
                    st.session_state.input_key_counter += 1
                
                st.rerun()
    
    # Show conversation ended message if applicable
    elif len(st.session_state.chat_history) > 0 and st.session_state.get('conversation_ended', False):
        st.markdown('<div style="margin-top: 2rem; border-top: 1px solid #e0e0e0; padding-top: 1rem;"></div>', unsafe_allow_html=True)
        st.info("💬 This conversation has ended. Use the sidebar to start a new conversation if you have more questions!")

if __name__ == "__main__":
    main()
