import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Bedrock Configuration
AWS_REGION = "us-east-1"
BEDROCK_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"

# Jira / Confluence API config
JIRA_URL = os.getenv("JIRA_BASE_URL", "https://modeln.atlassian.net")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_USER = os.getenv("JIRA_USERNAME")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://modeln.atlassian.net/wiki")

# Mindtouch Configuration
MINDTOUCH_API_KEY = os.getenv("MINDTOUCH_API_KEY")
MINDTOUCH_API_SECRET = os.getenv("MINDTOUCH_API_SECRET")
MINDTOUCH_USERNAME = os.getenv("MINDTOUCH_USERNAME", "=customer")  # Default to customer-facing content

# Vector Store Configuration
VECTOR_STORE_PATH = "vector_store"
SIMILARITY_THRESHOLD = 0.3# Lowered for better matching with enhanced classification

# Enhanced LLM Classification Prompt with better context and examples
CLASSIFICATION_PROMPT = """
You are an intelligent query classifier with deep understanding of enterprise knowledge management systems. 

Analyze the user query and determine the most appropriate knowledge source based on these comprehensive criteria:

**AVAILABLE SOURCES:**

1. **JIRA** - Issues, Tickets, and Project Management
   - Use for: bugs, issues, tasks, incidents, service requests, project tracking
   - Keywords: "error", "issue", "problem", "ticket", "bug", "failed", "not working", "broken"
   - Examples: "API returning 500 error", "User cannot login", "Performance issue with dashboard"

2. **CONFLUENCE** - Documentation and Knowledge Base  
   - Use for: documentation, processes, procedures, meeting notes, policies, guides
   - Keywords: "how to", "process", "procedure", "documentation", "guide", "policy", "meeting"
   - Examples: "How to deploy to production", "Onboarding process", "API documentation"

3. **MINDTOUCH** - Product Help and User Guides
   - Use for: product features, user guides, troubleshooting, customer-facing help
   - Keywords: "feature", "how does", "user guide", "help with", "tutorial", "getting started"
   - Examples: "How to use the reporting feature", "Getting started guide", "Feature documentation"

**CLASSIFICATION RULES:**
- If query mentions specific errors, failures, or technical issues → JIRA
- If query asks about processes, procedures, or general documentation → CONFLUENCE  
- If query asks about product features, usage, or customer help → MINDTOUCH
- If uncertain between CONFLUENCE and MINDTOUCH, prefer CONFLUENCE for internal topics, MINDTOUCH for user-facing topics
- Default fallback: CONFLUENCE

User Query: {query}

Respond with exactly one word: JIRA, CONFLUENCE, or MINDTOUCH

Classification:"""
