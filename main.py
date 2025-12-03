"""
nQuiry - Intelligent Query Processing System
New Flow: JIRA (organization-specific) → MindTou            else:
                # Use Bedrock to evaluate if JIRA results are sufficient
                query = state.get('query', '')
                bedrock_decision = self.analyze_with_bedrock(query, search_results, 'JIRA')
                
                if bedrock_decision.get('action') == 'create_ticket':
                    print("📖 JIRA results insufficient - fallback to MindTouch")
                    return "search_mindtouch"
                else:
                    print("🎯 JIRA results sufficient - formatting response")
                    return "format_response"→ Create Ticket
"""

from typing import Dict, List, Any, Optional, TypedDict, Tuple
import boto3
import json
from datetime import datetime
from langgraph.graph import StateGraph, START, END

from semantic_search import SemanticSearch
from response_formatter import ResponseFormatter
from ticket_creator import TicketCreator
from tools.mindtouch_tool import MindTouchTool
from tools.jira_tool import JiraTool
from tools.zendesk_tool import ZendeskTool
from tools.azure_blob_tool import AzureBlobSharePointTool
from chat_history_manager import ChatHistoryManager
from continuous_learning_manager import get_learning_manager
from customer_role_manager import CustomerRoleMappingManager

# Configuration
FALLBACK_SEARCH_ENABLED = False  # Disabled - relying on new flow


class QueryState(TypedDict):
    """State model for the LangGraph workflow"""
    query: str
    context: Optional[str]
    user_email: Optional[str]
    classified_source: Optional[str]
    search_results: List[Dict]
    similarity_scores: List[float]
    formatted_response: Optional[str]
    ticket_created: Optional[str]
    error: Optional[str]
    api_results: Optional[Dict]


class IntelligentQueryProcessor:
    """
    LangGraph-based intelligent query processor using custom REST API tools
    """

    def __init__(self, customer_email=None, streamlit_mode=False):
        # Initialize basic components
        self.semantic_search = SemanticSearch()
        self.response_formatter = ResponseFormatter()
        self.ticket_creator = TicketCreator()
        self.chat_history_manager = ChatHistoryManager()
        self.streamlit_mode = streamlit_mode
        
        # 🧠 Initialize continuous learning manager
        self.learning_manager = get_learning_manager()
        print("🧠 Continuous Learning Manager integrated")

        # Get customer email upfront for all queries (required for customer identification)
        if customer_email:
            # Use provided email (for API/web server mode)
            print(f"🎯 Using provided customer email: {customer_email}")
        elif not streamlit_mode:  # Skip interactive prompt in Streamlit
            print("🔐 Customer Authentication Required")
            print("=" * 40)
            print("💡 Please provide your email for customer identification and role-based access")
            customer_email = MindTouchTool.get_customer_email_from_input()
        else:
            # Streamlit mode - email should be provided via other means
            customer_email = "demo@example.com"  # Fallback

        # Initialize customer role manager for support domain detection
        self.customer_role_manager = CustomerRoleMappingManager()
        
        # Debug: Show loaded support domains
        support_domains = self.customer_role_manager.get_support_domains()
        print(f"🔍 Loaded support domains: {support_domains}")
        
        # Temporary: Add modeln.com as support domain for testing if not present
        if customer_email and 'modeln.com' in customer_email and 'modeln.com' not in support_domains:
            print(f"⚠️ Adding modeln.com as support domain for testing")
            self.customer_role_manager.support_domains.add('modeln.com')
        
        # Check if this is a support domain (triggers Zendesk workflow)
        self.is_support_domain = self.customer_role_manager.is_support_domain(customer_email)
        print(f"🎯 Domain check for {customer_email}: is_support_domain = {self.is_support_domain}")
        
        # CRITICAL: Prevent dual workflow execution
        if self.is_support_domain:
            print(f"🔒 ZENDESK WORKFLOW ONLY - JIRA tools disabled")
        else:
            print(f"🔒 JIRA WORKFLOW ONLY - Zendesk tools disabled")
        
        # Initialize tools based on domain type
        if self.is_support_domain:
            # Zendesk workflow: Zendesk + Azure Blob + MindTouch → Zendesk tickets
            print("🔧 Building ZENDESK workflow (support domain)")
            try:
                self.zendesk_tool = ZendeskTool()
                print(f"✅ Zendesk tool initialized for support domain")
            except Exception as e:
                print(f"⚠️ Failed to initialize Zendesk tool: {e}")
                self.zendesk_tool = None
            
            try:
                self.azure_blob_tool = AzureBlobSharePointTool()
                print(f"✅ Azure Blob tool initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize Azure Blob tool: {e}")
                self.azure_blob_tool = None
                
            # Explicitly disable JIRA for support domains
            self.jira_tool = None
        else:
            # Regular workflow: JIRA + MindTouch → JIRA tickets
            print(f"🔧 Building JIRA workflow (regular domain)")
            print(f"🔧 Initializing JIRA workflow tools...")
            self.jira_tool = JiraTool()
            
            # Explicitly disable Zendesk/Azure for regular domains
            self.zendesk_tool = None
            self.azure_blob_tool = None
            print(f"✅ JIRA workflow tools initialized")
        
        self.mindtouch_tool = MindTouchTool(customer_email=customer_email)

        # Store customer info (assumes method returns dict with organization/role/email)
        try:
            self.customer_info = self.mindtouch_tool.get_customer_info()
            org = self.customer_info.get("organization", "Unknown")
            role = self.customer_info.get("role", "Unknown")
            email = self.customer_info.get("email", customer_email)
        except Exception:
            # Fallback minimal info if mindtouch call fails
            self.customer_info = {"organization": "Unknown", "role": "Unknown", "email": customer_email}
            org = "Unknown"
            role = "Unknown"
            email = customer_email

        print(f"\n✅ nQuiry initialized for {org} customer")
        print(f"🎭 MindTouch Role: {role}")
        print(f"📧 Customer Email: {email}")
        
        if self.is_support_domain:
            print(f"🎫 Workflow: Zendesk + Azure Blob + MindTouch → Zendesk Tickets")
        else:
            print(f"🔄 Workflow: JIRA ({org}) + MindTouch → JIRA Tickets")

        # Initialize the LangGraph
        self.graph = self._build_langgraph()

        # Initialize AWS Bedrock client
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')  # Replace with your region

    def _build_langgraph(self):
        """Build the LangGraph workflow with domain-based routing"""

        workflow = StateGraph(dict)

        if self.is_support_domain:
            # Zendesk workflow: Search Zendesk, Azure Blob, and MindTouch
            workflow.add_node("search_zendesk", self.search_zendesk_node)
            workflow.add_node("search_azure_blob", self.search_azure_blob_node)
            workflow.add_node("search_mindtouch", self.search_mindtouch_node)
            workflow.add_node("format_response", self.format_response_node)
            workflow.add_node("create_zendesk_ticket", self.create_zendesk_ticket_node)
            
            # Sequential search flow for Zendesk domains
            workflow.add_edge(START, "search_zendesk")
            workflow.add_edge("search_zendesk", "search_azure_blob")
            workflow.add_conditional_edges(
                "search_azure_blob",
                self.should_search_mindtouch_after_azure,
                {
                    "search_mindtouch": "search_mindtouch",
                    "format_response": "format_response"
                }
            )
            workflow.add_edge("search_mindtouch", "format_response")
            workflow.add_edge("format_response", END)
        else:
            # Regular JIRA workflow
            workflow.add_node("search_jira", self.search_jira_node)
            workflow.add_node("search_mindtouch", self.search_mindtouch_node)
            workflow.add_node("format_response", self.format_response_node)
            workflow.add_node("create_ticket", self.create_ticket_node)

            # Define the routing logic for regular workflow
            def should_fallback_to_mindtouch(state) -> str:
                """Always search MindTouch to combine with JIRA results for comprehensive response"""
                search_results = state.get('search_results', [])
                
                if not search_results:
                    print("📖 No JIRA results found - fallback to MindTouch")
                    return "search_mindtouch"
                else:
                    print("📖 JIRA results found - also searching MindTouch for comprehensive response")
                    return "search_mindtouch"

            def should_create_ticket_or_format(state) -> str:
                """Decide whether to create ticket or format response"""
                # Always format response first - the formatter will decide about ticket options
                print("📝 Formatting comprehensive response with search results")
                return "format_response"

            # Define edges for regular workflow
            workflow.add_edge(START, "search_jira")
            
            workflow.add_conditional_edges(
                "search_jira",
                should_fallback_to_mindtouch,
                {
                    "search_mindtouch": "search_mindtouch",
                    "format_response": "format_response"
                }
            )
            
            workflow.add_conditional_edges(
                "search_mindtouch", 
                should_create_ticket_or_format,
                {
                    "format_response": "format_response"
                }
            )
            
            workflow.add_edge("format_response", END)

        return workflow.compile()

    def search_jira_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Search JIRA for organization-specific tickets and rank results"""
        # CRITICAL: Only execute for non-support domains
        if self.is_support_domain:
            print("🚫 JIRA search skipped - this is a support domain (should use Zendesk)")
            state['search_results'] = []
            state['similarity_scores'] = []
            return state
            
        try:
            customer_org = self.customer_info.get("organization", "Unknown")
            query = state.get('query', '')
            
            print(f"🎫 Searching JIRA for {customer_org} specific tickets...")
            print(f"📝 Query: '{query}'")

            # Search for organization-specific issues using custom JIRA tool
            issues = self.jira_tool.search_issues_by_organization(query, customer_org, limit=20)

            if issues:
                print(f"📊 Found {len(issues)} JIRA issues for {customer_org}")
                
                # Process and rank results with semantic search
                documents = []
                for issue in issues:
                    doc = {
                        'key': issue.get('key', ''),
                        'title': issue.get('summary', ''),
                        'content': issue.get('content', ''),
                        'status': issue.get('status', ''),
                        'priority': issue.get('priority', ''),
                        'assignee': issue.get('assignee', ''),
                        'created': issue.get('created', ''),
                        'updated': issue.get('updated', ''),
                        'labels': issue.get('labels', []),
                        'resolution': issue.get('resolution', ''),
                        'organization': issue.get('organization_match', ''),
                        'meta': issue
                    }
                    documents.append(doc)
                
                # Rank documents with semantic search
                print("� Ranking JIRA results with semantic search...")
                ranked_docs, scores = self.semantic_search.search_documents(
                    documents, query, learning_manager=self.learning_manager)
                
                # Combine ranked_docs and scores into a list of tuples
                state['search_results'] = list(zip(ranked_docs, scores))
                state['last_search_source'] = 'JIRA'  # Track the source for response formatting
                print(f"✅ Ranked {len(ranked_docs)} JIRA results")
                
                # Display brief summary of top results
                for i, (doc, score) in enumerate(state['search_results'][:3]):
                    print(f"   {i+1}. {doc.get('key', 'Unknown')}: {doc.get('title', 'No title')[:60]}... (Score: {score:.2f})")
                    
            else:
                state['search_results'] = []
                state['similarity_scores'] = []
                print(f"⚠️  No JIRA issues found for organization: {customer_org}")

        except Exception as e:
            print(f"❌ Error searching JIRA: {e}")
            state['error'] = f"JIRA search error: {e}"
            state['search_results'] = []
            state['similarity_scores'] = []

        return state

    def search_mindtouch_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Search MindTouch and rank results with semantic search"""
        try:
            query = state.get('query', '')
            print(f"📄 Searching MindTouch via REST API...")
            print(f"🎭 Using role: {self.customer_info.get('role')} for {self.customer_info.get('organization')}")
            
            # Add performance tracking
            import time
            mindtouch_start = time.time()

            # Get MindTouch documents - this returns formatted LLM response
            documents = self.mindtouch_tool.search_pages(query, limit=20)
            
            if documents:
                mindtouch_elapsed = time.time() - mindtouch_start
                print(f"📊 MindTouch search completed: {len(documents)} pages in {mindtouch_elapsed:.2f}s")
                
                # Check if we have existing JIRA results to combine with
                existing_results = state.get('search_results', [])
                existing_scores = state.get('similarity_scores', [])
                
                # MindTouch returns already processed/formatted documents
                # Convert to the expected format: list of (document, similarity_score) tuples
                mindtouch_scores = [doc.get('score', 1.0) for doc in documents]
                mindtouch_results = list(zip(documents, mindtouch_scores))
                
                if existing_results:
                    # Combine existing results with MindTouch results
                    source_name = "Zendesk/Azure Blob" if self.is_support_domain else "JIRA"
                    print(f"🔗 Combining {len(existing_results)} {source_name} results with {len(mindtouch_results)} MindTouch results")
                    state['search_results'] = existing_results + mindtouch_results
                    state['similarity_scores'] = existing_scores + mindtouch_scores
                    state['last_search_source'] = 'MULTI'  # Indicate mixed sources
                else:
                    # Only MindTouch results
                    state['search_results'] = mindtouch_results
                    state['similarity_scores'] = mindtouch_scores
                    state['last_search_source'] = 'MINDTOUCH'
                
                print(f"✅ Combined results ready for formatting")
            else:
                # No MindTouch results, but check if we have existing results
                existing_results = state.get('search_results', [])
                if existing_results:
                    source_name = "Zendesk/Azure Blob" if self.is_support_domain else "JIRA"
                    print(f"⚠️  No MindTouch pages found, but {source_name} results available")
                    state['last_search_source'] = 'ZENDESK_AZURE' if self.is_support_domain else 'JIRA'
                    print(f"✅ {source_name} results ready for formatting")
                else:
                    search_sources = "Zendesk, Azure Blob, or MindTouch" if self.is_support_domain else "JIRA or MindTouch"
                    print(f"⚠️  No results found in {search_sources}")
                    state['search_results'] = []
                    state['similarity_scores'] = []

        except Exception as e:
            print(f"❌ Error searching MindTouch: {e}")
            state['error'] = f"MindTouch search error: {e}"
            state['search_results'] = []
            state['similarity_scores'] = []

        return state

    def search_zendesk_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Search Zendesk tickets for support domain users"""
        # CRITICAL: Only execute for support domains
        if not self.is_support_domain:
            print("🚫 Zendesk search skipped - not a support domain")
            state['search_results'] = []
            state['similarity_scores'] = []
            return state
            
        try:
            if not self.zendesk_tool:
                print("⚠️  Zendesk tool not available")
                state['search_results'] = []
                state['similarity_scores'] = []
                return state
                
            query = state.get('query', '')
            
            print(f"🎫 Searching ALL Zendesk support tickets...")
            print(f"📝 Query: '{query}'")

            # Search ALL tickets using Zendesk tool (not organization-specific)
            tickets = self.zendesk_tool.search_tickets(query, organization=None, limit=15)

            if tickets:
                print(f"📊 Found {len(tickets)} Zendesk tickets total")
                
                # Process and rank results with semantic search
                documents = []
                for ticket in tickets:
                    doc = {
                        'key': ticket.get('key', ''),
                        'title': ticket.get('summary', ''),
                        'content': ticket.get('content', ''),
                        'status': ticket.get('status', ''),
                        'priority': ticket.get('priority', ''),
                        'assignee': ticket.get('assignee', ''),
                        'created': ticket.get('created', ''),
                        'updated': ticket.get('updated', ''),
                        'labels': ticket.get('labels', []),
                        'type': ticket.get('type', ''),
                        'organization': ticket.get('organization_match', ''),
                        'platform': 'Zendesk',
                        'meta': ticket
                    }
                    documents.append(doc)
                
                # Rank documents with semantic search
                print("🧠 Ranking Zendesk results with semantic search...")
                ranked_docs, scores = self.semantic_search.search_documents(
                    documents, query, learning_manager=self.learning_manager)
                
                # Store results as tuples
                state['search_results'] = list(zip(ranked_docs, scores))
                state['last_search_source'] = 'ZENDESK'
                print(f"✅ Ranked {len(ranked_docs)} Zendesk results")
                
                # Display brief summary of top results
                for i, (doc, score) in enumerate(state['search_results'][:3]):
                    print(f"   {i+1}. {doc.get('key', 'Unknown')}: {doc.get('title', 'No title')[:60]}... (Score: {score:.2f})")
                    
            else:
                state['search_results'] = []
                state['similarity_scores'] = []
                print(f"⚠️  No Zendesk tickets found for query: '{query}'")

        except Exception as e:
            print(f"❌ Error searching Zendesk: {e}")
            state['error'] = f"Zendesk search error: {e}"
            state['search_results'] = []
            state['similarity_scores'] = []

        return state

    def search_azure_blob_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Search Azure Blob Storage for documents - Support domains only"""
        # CRITICAL: Only execute for support domains
        if not self.is_support_domain:
            print("🚫 Azure Blob search skipped - not a support domain")
            return state
            
        try:
            if not self.azure_blob_tool:
                print("⚠️  Azure Blob tool not available")
                return state
                
            query = state.get('query', '')
            print(f"🗂️  Searching Azure Blob Storage...")
            print(f"📝 Query: '{query}'")

            # Search for documents in Azure Blob Storage (get more results for better semantic ranking)
            documents = self.azure_blob_tool.search_documents(query, max_results=25)

            if documents:
                print(f"📊 Found {len(documents)} documents in Azure Blob Storage")
                
                # Process and rank results with semantic search
                blob_docs = []
                for doc in documents:
                    blob_doc = {
                        'key': doc.get('name', ''),
                        'title': doc.get('name', ''),
                        'content': doc.get('content', ''),
                        'url': doc.get('url', ''),
                        'last_modified': doc.get('last_modified', ''),
                        'size': doc.get('size', ''),
                        'type': doc.get('content_type', ''),
                        'platform': 'Azure Blob',
                        'meta': doc
                    }
                    blob_docs.append(blob_doc)
                
                # Rank documents with semantic search
                print("🧠 Ranking Azure Blob results with semantic search...")
                ranked_docs, scores = self.semantic_search.search_documents(
                    blob_docs, query, learning_manager=self.learning_manager)
                
                # Combine with existing Zendesk results
                existing_results = state.get('search_results', [])
                existing_scores = state.get('similarity_scores', [])
                
                azure_results = list(zip(ranked_docs, scores))
                
                if existing_results:
                    print(f"🔗 Combining {len(existing_results)} Zendesk results with {len(azure_results)} Azure Blob results")
                    state['search_results'] = existing_results + azure_results
                    state['similarity_scores'] = existing_scores + scores
                    state['last_search_source'] = 'MULTI'
                else:
                    state['search_results'] = azure_results
                    state['similarity_scores'] = scores
                    state['last_search_source'] = 'AZURE_BLOB'
                
                print(f"✅ Ranked {len(ranked_docs)} Azure Blob results")
                
            else:
                print("⚠️  No documents found in Azure Blob Storage")

        except Exception as e:
            print(f"❌ Error searching Azure Blob: {e}")
            state['error'] = f"Azure Blob search error: {e}"

        return state

    def should_search_mindtouch_after_azure(self, state: Dict[str, Any]) -> str:
        """Conditional router: Check if MindTouch search is needed after Azure Blob search"""
        
        search_results = state.get('search_results', [])
        similarity_scores = state.get('similarity_scores', [])
        query = state.get('query', '').lower()
        
        # Check if Azure Blob found good quality results
        if search_results and similarity_scores:
            quality_results = 0
            high_relevance_results = 0
            workbench_results = 0
            
            for i, result in enumerate(search_results):
                if i < len(similarity_scores):
                    score = similarity_scores[i]
                    
                    # Extract result info (handle tuple format from semantic search)
                    if isinstance(result, tuple):
                        doc_info = result[0]
                        content = doc_info.get('content', '')
                        title = doc_info.get('title', '')
                    else:
                        content = result.get('content', '')
                        title = result.get('title', '')
                    
                    content_length = len(content)
                    title_lower = title.lower()
                    
                    # Check for workbench-specific content
                    workbench_keywords = ['workbench', 'upload', 'validation', 'procedure']
                    if any(keyword in title_lower for keyword in workbench_keywords):
                        workbench_results += 1
                    
                    # Quality scoring
                    if score > 0.5 or content_length > 150:
                        quality_results += 1
                    
                    if score > 0.6 or (content_length > 100 and any(term in title_lower for term in query.split())):
                        high_relevance_results += 1
            
            # Decision logic
            if high_relevance_results >= 1:  # At least 1 high relevance result
                print(f"🎯 Azure Blob found {high_relevance_results} high-relevance results - skipping MindTouch")
                return "format_response"
            elif workbench_results >= 1 and quality_results >= 2:  # Workbench content with decent quality
                print(f"🎯 Azure Blob found {workbench_results} workbench results - skipping MindTouch")
                return "format_response"
            elif quality_results >= 3:  # Multiple decent results
                print(f"🎯 Azure Blob found {quality_results} quality results - skipping MindTouch")
                return "format_response"
        
        print("📄 Azure Blob results insufficient - continuing to MindTouch")
        return "search_mindtouch"

    def create_zendesk_ticket_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Create Zendesk ticket for support domain users"""
        try:
            if not self.zendesk_tool:
                print("⚠️  Zendesk tool not available")
                state['error'] = "Zendesk tool not available"
                return state
                
            query = state.get('query', '')
            customer_email = self.customer_info.get('email', '')
            
            print(f"🎫 Creating Zendesk ticket for support domain user...")
            
            # Prepare ticket data
            ticket_data = {
                'summary': f"Support Request: {query[:80]}{'...' if len(query) > 80 else ''}",
                'description': f"Customer Query: {query}\n\nCustomer Email: {customer_email}\nOrganization: {self.customer_info.get('organization', 'Unknown')}",
                'priority': 'normal',
                'type': 'question',
                'tags': ['nquiry-auto', 'support-request']
            }
            
            # Create ticket using Zendesk tool
            result = self.zendesk_tool.create_ticket(ticket_data)
            
            if result.get('status') == 'success':
                state['ticket_created'] = result
                print(f"✅ Zendesk ticket created: {result.get('ticket_key', 'Unknown')}")
            else:
                state['error'] = f"Failed to create Zendesk ticket: {result.get('message', 'Unknown error')}"
                print(f"❌ {state['error']}")

        except Exception as e:
            print(f"❌ Error creating Zendesk ticket: {e}")
            state['error'] = f"Zendesk ticket creation error: {e}"

        return state



    def analyze_with_bedrock(self, query: str, search_results: List[Tuple[Dict, float]], source: str = "MULTI", context: str = "") -> Dict:
        """
        Use AWS Bedrock to analyze search results and decide next steps.
        """
        try:
            # First, format the search results into a readable format
            formatted_response = self.response_formatter.format_search_results(query, search_results, source, context)

            print("🤖 Formatted Bedrock Response:")
            print(formatted_response)

            # Now use LLM to evaluate if this response adequately answers the query
            evaluation_prompt = f"""
You are an expert system evaluating whether a search result adequately answers a user's query.

{'CONVERSATION CONTEXT:' + chr(10) + context + chr(10) + chr(10) if context else ''}USER QUERY: {query}

SEARCH RESULT RESPONSE:
{formatted_response}

Please analyze the above response and determine if it provides actionable resolution steps.{' Consider the conversation context when evaluating the response.' if context else ''}

The response should be considered INSUFFICIENT if it contains phrases like:
- "Unfortunately, no specific resolution steps are provided"
- "I cannot provide actionable steps"
- "no resolution details are included"
- "More context is needed"
- "Further investigation...is required"
- "does not contain complete details"
- "without more details"
- Similar phrases indicating lack of actionable information

The response should be considered SUFFICIENT only if it provides:
- Clear, step-by-step resolution instructions
- Specific actions the user can take
- Complete troubleshooting guidance
- Definitive answers to the user's question{' - Proper follow-up to previous conversation points' if context else ''}

Respond with ONLY one of these two options:
- SUFFICIENT: if the response provides clear, actionable resolution steps
- INSUFFICIENT: if the response lacks specific resolution steps or contains uncertainty phrases

Your response should be a single word: either SUFFICIENT or INSUFFICIENT.
"""

            # Call Bedrock to evaluate the response quality
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ]
            }
            
            # Add timeout handling for Bedrock calls
            import time
            start_time = time.time()
            
            response = self.response_formatter.bedrock_client.invoke_model(
                modelId=self.response_formatter.model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            elapsed_time = time.time() - start_time
            print(f"⏱️  Bedrock evaluation took {elapsed_time:.2f} seconds")
            
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                decision = response_body['content'][0]['text'].strip().upper()
                
                if "SUFFICIENT" in decision:
                    print("🤖 Bedrock evaluation: Response is SUFFICIENT")
                    return {"action": "format_response", "formatted_response": formatted_response}
                else:
                    print("🤖 Bedrock evaluation: Response is INSUFFICIENT")
                    return {"action": "create_ticket", "formatted_response": formatted_response}
            else:
                print("❌ No response from Bedrock evaluation")
                return {"action": "create_ticket", "formatted_response": formatted_response}

        except Exception as e:
            print(f"❌ Error invoking Bedrock model: {e}")
            return {"action": "error", "error": str(e)}

    def format_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Format the search results with Bedrock reasoning"""
        try:
            print("✍️  Formatting response with AWS Bedrock reasoning...")

            search_results = state.get('search_results', [])
            query = state.get('query', '')
            context = state.get('context', '')

            # Handle case where no search results were found
            if not search_results:
                if self.is_support_domain:
                    print("⚠️  No search results found in Zendesk or Azure Blob")
                    state['formatted_response'] = f"I searched through Zendesk tickets and documentation but couldn't find specific information related to your query: **{query}**\n\n❓ Since I wasn't able to find relevant information, would you like me to create a support ticket so our technical team can assist you directly?"
                else:
                    print("⚠️  No search results found in JIRA or MindTouch")
                    state['formatted_response'] = f"I searched through JIRA tickets and documentation but couldn't find specific information related to your query: **{query}**\n\n❓ Since I wasn't able to find relevant information, would you like me to create a support ticket so our technical team can assist you directly?"
                state['ticket_creation_suggested'] = True
                return state

            # Determine the source based on state or results
            source = state.get('last_search_source', 'MULTI')
            
            # Use AWS Bedrock to analyze the results
            bedrock_decision = self.analyze_with_bedrock(query, search_results, source, context)

            if bedrock_decision.get('action') == 'create_ticket':
                print("🤖 Bedrock suggests creating a ticket due to insufficient information.")
                state['formatted_response'] = "The results do not fully address your query. Would you like to create a ticket?"
                state['ticket_creation_suggested'] = True
            elif bedrock_decision.get('action') == 'format_response':
                print("🤖 Bedrock suggests the results are sufficient.")
                formatted_response = self.response_formatter.format_search_results(
                    query=query,
                    results=search_results,
                    source=state.get('classified_source', ''),
                    context=context
                )
                
                # Always offer ticket creation for all responses
                source = state.get('last_search_source', state.get('classified_source', ''))
                
                if self.is_support_domain:
                    # Support domain responses (Zendesk + Azure Blob)
                    if source == 'MULTI':
                        print("📋 Combined Zendesk + Azure Blob response provided - offering ticket creation option")
                        state['formatted_response'] = formatted_response + "\n\n❓ This response combines information from Zendesk tickets and documentation. If you are not satisfied with this resolution or need further assistance, would you like me to create a support ticket for you?"
                    elif source == 'ZENDESK':
                        print("📋 Zendesk response provided - offering ticket creation option")
                        state['formatted_response'] = formatted_response + "\n\n❓ This response is based on Zendesk ticket data. If you are not satisfied with this resolution or need further assistance, would you like me to create a support ticket for you?"
                    else:
                        print("📋 Support documentation response provided - offering ticket creation option")
                        state['formatted_response'] = formatted_response + "\n\n❓ This response is based on support documentation. If you are not satisfied with this resolution or need further assistance, would you like me to create a support ticket for you?"
                else:
                    # Regular domain responses (JIRA + MindTouch)
                    if source == 'JIRA':
                        print("📋 JIRA response provided - offering ticket creation option")
                        state['formatted_response'] = formatted_response + "\n\n❓ This response is based on JIRA ticket data. If you are not satisfied with this resolution or need further assistance, would you like me to create a support ticket for you?"
                    elif source == 'MULTI':
                        print("📋 Combined JIRA + MindTouch response provided - offering ticket creation option")
                        state['formatted_response'] = formatted_response + "\n\n❓ This response combines information from JIRA tickets and documentation. If you are not satisfied with this resolution or need further assistance, would you like me to create a support ticket for you?"
                    elif source == 'MINDTOUCH':
                        print("📋 MindTouch response provided - offering ticket creation option")
                        state['formatted_response'] = formatted_response + "\n\n❓ This response is based on documentation. If you are not satisfied with this resolution or need further assistance, would you like me to create a support ticket for you?"
                    else:
                        print("📋 General response provided - offering ticket creation option")
                    state['formatted_response'] = formatted_response + "\n\n❓ If you are not satisfied with this response, would you like me to create a support ticket for further assistance?"
                
                # Always suggest ticket creation
                state['ticket_creation_suggested'] = True
                return state
            else:
                print("❌ Bedrock returned an error.")
                state['error'] = bedrock_decision.get('error', 'Unknown error')
                state['formatted_response'] = "❌ Error analyzing results with Bedrock."

            print(f"✅ Response formatted successfully with Bedrock decision: {bedrock_decision.get('action')}")

        except Exception as e:
            print(f"❌ Error formatting response with Bedrock: {e}")
            state['error'] = f"Response formatting error: {e}"
            state['formatted_response'] = f"Error formatting response: {e}"

        return state

    def create_ticket_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Create support ticket (JIRA or Zendesk based on domain)"""
        try:
            # Get user information from state
            user_email = state.get('user_email', '')
            query = state.get('query', '')
            conversation_history = state.get('history', [])
            
            print(f"🎫 Creating support ticket for query: {query}")
            
            if self.is_support_domain and self.zendesk_tool:
                # Create real Zendesk ticket for support domains
                print("🎫 Creating Zendesk ticket...")
                
                # Prepare conversation context for ticket
                conversation_context = self._prepare_conversation_context(conversation_history, query)
                
                # Create ticket data
                ticket_data = {
                    "subject": f"Support Request: {query[:100]}",
                    "description": conversation_context,
                    "requester_email": user_email,
                    "priority": "normal",
                    "type": "question",
                    "tags": ["api", "automated", "support"]
                }
                
                # Create ticket in Zendesk
                ticket_result = self.zendesk_tool.create_ticket(ticket_data)
                
                if ticket_result.get('success'):
                    ticket_info = ticket_result['ticket']
                    ticket_id = ticket_info.get('id')
                    ticket_url = ticket_info.get('url', '')
                    
                    # Format success response
                    ticket_response = f"""✅ **Zendesk Support Ticket Created Successfully!**

🎫 **Ticket ID:** {ticket_id}
📧 **Requester:** {user_email}
🔗 **Ticket URL:** {ticket_url}

**Subject:** {ticket_data['subject']}

**Description:**
{ticket_data['description'][:300]}{'...' if len(ticket_data['description']) > 300 else ''}

🕒 **Status:** Open
⏱️ **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Our support team will review your ticket and respond soon. You can track progress using the ticket ID or URL above."""
                    
                    state['ticket_created'] = {
                        'success': True,
                        'ticket_id': ticket_id,
                        'ticket_url': ticket_url,
                        'platform': 'Zendesk'
                    }
                    print(f"✅ Zendesk ticket created successfully: {ticket_id}")
                    
                else:
                    # Fallback if Zendesk creation fails
                    error_msg = ticket_result.get('error', 'Unknown error')
                    print(f"❌ Zendesk ticket creation failed: {error_msg}")
                    ticket_response = f"❌ Failed to create Zendesk ticket: {error_msg}\n\nPlease contact support directly."
                    state['ticket_created'] = {'success': False, 'error': error_msg}
                    
            else:
                # Create simulated JIRA ticket for regular domains
                print("🎫 Creating simulated JIRA ticket...")
                ticket_response = self.response_formatter.create_simulated_ticket(
                    query=query,
                    user_email=user_email,
                    additional_description="User requested ticket creation after insufficient search results"
                )
                state['ticket_created'] = {'success': True, 'platform': 'JIRA', 'simulated': True}
            
            state['formatted_response'] = ticket_response
            
        except Exception as e:
            print(f"❌ Error creating support ticket: {e}")
            state['error'] = f"Ticket creation error: {e}"
            state['formatted_response'] = f"❌ Error creating support ticket: {e}"

        return state

    def _prepare_conversation_context(self, history: List[Dict], current_query: str) -> str:
        """Prepare conversation context for ticket creation"""
        context_parts = []
        
        # Add current query
        context_parts.append(f"**Current Issue:**\n{current_query}\n")
        
        # Add conversation history if available
        if history and len(history) > 0:
            context_parts.append("**Conversation History:**")
            
            # Get last few messages for context (limit to avoid too long tickets)
            recent_messages = history[-5:] if len(history) > 5 else history
            
            for i, msg in enumerate(recent_messages):
                role = msg.get('role', 'user')
                message = msg.get('message', msg.get('content', ''))
                timestamp = msg.get('timestamp', '')
                
                if role == 'user':
                    context_parts.append(f"\n**User ({timestamp}):** {message}")
                elif role == 'assistant':
                    context_parts.append(f"\n**Assistant ({timestamp}):** {message}")
        
        # Add system information
        context_parts.append(f"\n\n**Technical Details:**")
        context_parts.append(f"- Domain: {'Support Domain (Zendesk)' if self.is_support_domain else 'Regular Domain (JIRA)'}")
        context_parts.append(f"- Organization: {self.customer_info.get('organization', 'Unknown')}")
        context_parts.append(f"- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return '\n'.join(context_parts)
    
    def create_ticket_node_interactive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Create support ticket with user interaction (legacy)"""
        try:
            search_results = state.get('search_results', [])
            similarity_scores = state.get('similarity_scores', [])
            
            # Determine source based on current workflow stage
            if search_results:
                first_result = search_results[0] if isinstance(search_results, list) and search_results else {}
                if isinstance(first_result, dict) and first_result.get('key') and 'PROJ-' in str(first_result.get('key', '')):
                    source = 'JIRA'
                else:
                    source = 'MINDTOUCH'
            else:
                source = 'UNKNOWN'

            # If there are search results, show them first (console-only preview)
            if search_results:
                print(f"\n📊 Found {len(search_results)} related {source} results:")
                
                # Check if search_results is already in tuple format (document, score)
                if search_results and isinstance(search_results[0], tuple) and len(search_results[0]) == 2:
                    # Already in the correct format
                    results_with_scores = search_results
                else:
                    # Convert from list of documents to list of tuples
                    results_with_scores = list(zip(search_results, similarity_scores))
                    
                formatted_results = self.response_formatter.format_search_results(
                    query=state.get('query', ''),
                    results=results_with_scores,
                    source=source,
                    context=state.get('context', '')
                )
                print(formatted_results)

            # Ask user if they want to create a new ticket
            print("\n🎫 Would you like to create a new JIRA ticket for this query?")
            create_ticket = input("Create ticket? (y/n): ")

            if create_ticket in ['y', 'yes', '1', 'true']:
                print("🎫 Creating support ticket via JIRA REST API...")

                # Get ticket information from user
                ticket_data = self.ticket_creator.get_ticket_fields_from_user(state.get('query', ''))

                if self.ticket_creator.validate_ticket_data(ticket_data):
                    # Create ticket using custom JIRA tool
                    ticket_key = self.jira_tool.create_issue(
                        project_key=ticket_data['project_key'],
                        summary=ticket_data['summary'],
                        issue_type=ticket_data['issue_type'],
                        description=ticket_data['description'],
                        priority=ticket_data['priority'],
                        assignee=ticket_data.get('assignee'),
                        labels=ticket_data.get('labels', [])
                    )

                    if ticket_key:
                        state['ticket_created'] = ticket_key
                        state['formatted_response'] = (
                            f"\n🎫 Support Ticket Created Successfully!\n\n"
                            f"Ticket Key: {ticket_key}\n"
                            f"Summary: {ticket_data['summary']}\n"
                            f"Priority: {ticket_data['priority']}\n\n"
                            f"Your request has been logged and will be reviewed by our support team.\n"
                            f"You can track the progress using the ticket key: {ticket_key}\n"
                        )
                        print(f"✅ Ticket created: {ticket_key}")
                    else:
                        state['error'] = "Failed to create ticket"
                        state['formatted_response'] = "❌ Failed to create support ticket."
                else:
                    state['error'] = "Invalid ticket data"
                    state['formatted_response'] = "❌ Invalid ticket information provided."
            else:
                # User declined to create ticket
                if search_results:
                    # Check if search_results is already in tuple format (document, score)
                    if search_results and isinstance(search_results[0], tuple) and len(search_results[0]) == 2:
                        # Already in the correct format
                        results_with_scores = search_results
                    else:
                        # Convert from list of documents to list of tuples
                        results_with_scores = list(zip(search_results, similarity_scores))
                        
                    state['formatted_response'] = self.response_formatter.format_search_results(
                        query=state.get('query', ''),
                        results=results_with_scores,
                        source=state.get('classified_source', ''),
                        context=state.get('context', '')
                    )
                else:
                    state['formatted_response'] = "✅ No new ticket created. No relevant existing issues found."

        except Exception as e:
            print(f"❌ Error in ticket creation process: {e}")
            state['error'] = f"Ticket creation error: {e}"
            state['formatted_response'] = f"❌ Error in ticket creation process: {e}"

        return state

    def is_ticket_creation_request(self, query: str, previous_response: str = "") -> bool:
        """
        Detect if the user is requesting ticket creation, either in response to a prompt
        or as an explicit request after receiving information
        
        Args:
            query: Current user query
            previous_response: Previous bot response to check for ticket creation prompt
            
        Returns:
            True if this appears to be a ticket creation request
        """
        query_lower = query.lower().strip()
        
        # EXPLICIT TICKET CREATION REQUESTS - These work anytime, even without prompts
        explicit_ticket_requests = [
            'create ticket', 'create a ticket', 'make ticket', 'make a ticket',
            'submit ticket', 'submit a ticket', 'open ticket', 'open a ticket',
            'file ticket', 'file a ticket', 'ticket creation', 'support ticket',
            'create support ticket', 'open support ticket', 'submit support ticket',
            'i need a ticket', 'i want a ticket', 'can you create a ticket',
            'please create a ticket', 'help me create a ticket',
            'log a ticket', 'raise a ticket', 'escalate to ticket'
        ]
        
        # Check for explicit ticket creation requests (these work independently)
        for request in explicit_ticket_requests:
            if request in query_lower:
                print(f"🎫 Detected explicit ticket creation request: '{request}'")
                return True
        
        # AFFIRMATIVE RESPONSES TO SYSTEM PROMPTS
        affirmative_responses = [
            'yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay', 'alright',
            'please', 'yes please', 'go ahead', 'proceed', 'continue'
        ]
        
        # Check if previous response contained a ticket creation prompt
        if previous_response:
            ticket_prompts = [
                'would you like me to create a support ticket',
                'would you like to create a ticket',
                'create a support ticket for assistance',
                'would you like me to create',
                'create a ticket',
                'if you are not satisfied',
                'for further assistance'
            ]
            
            if any(prompt in previous_response.lower() for prompt in ticket_prompts):
                # If previous response had a ticket prompt and current query is affirmative
                if query_lower in affirmative_responses:
                    print(f"🎫 Detected affirmative response to ticket creation prompt")
                    return True
        
        # Check if query is a simple affirmative response without context (likely a yes to ticket creation)
        if query_lower in affirmative_responses and len(query_lower) <= 8:
            # Only treat as ticket request if there was some kind of suggestion in previous response
            if previous_response and ('ticket' in previous_response.lower() or 'assistance' in previous_response.lower()):
                print(f"🎫 Detected simple affirmative response with ticket context")
                return True
        
        return False

    def is_field_information_response(self, query: str, previous_response: str = "") -> bool:
        """
        Detect if the user is providing field information for ticket creation
        
        Args:
            query: Current user query
            previous_response: Previous bot response to check for field collection prompt
            
        Returns:
            True if this appears to be field information
        """
        # Check if previous response was asking for ticket fields
        if previous_response:
            field_indicators = [
                'additional information required',
                'please provide the following details',
                'area affected',
                'version affected',
                'reported environment',
                'please provide additional information',
                'which area is affected',
                'what version',
                'which environment'
            ]
            
            # Only proceed if previous response was asking for fields
            if any(indicator in previous_response.lower() for indicator in field_indicators):
                # Check if current response contains field-like information
                query_lower = query.lower()
                
                # Look for field patterns
                field_patterns = [
                    'area:', 'version:', 'environment:', 
                    'affected version', 'reported environment',
                    # Or version numbers
                    r'\d+\.\d+',
                    # Or environment names (but only if context suggests fields)
                    'production', 'staging', 'test', 'development'
                ]
                
                import re
                for pattern in field_patterns:
                    if ':' in pattern:
                        if pattern in query_lower:
                            return True
                    else:
                        if re.search(pattern, query_lower):
                            return True
                
                # If response has multiple lines or structured content, likely field info
                # But only if we already confirmed previous response was asking for fields
                if len(query.split('\n')) > 1:
                    return True
        
        return False

    def process_field_information_response(self, user_id: str, query: str, history: List = None) -> Dict[str, Any]:
        """
        Process user response containing field information for ticket creation
        
        Args:
            user_id: User identifier (email)
            query: Current user query containing field information
            history: Chat history to get context
            
        Returns:
            Response with field processing results or ticket creation
        """
        try:
            print(f"📝 Processing field information from user: {user_id}")
            
            # Parse field information from user response
            collected_fields = self.response_formatter.parse_field_response(query)
            
            # Find the original query from history
            original_query = ""
            if history and len(history) >= 3:
                # Look back through history to find the original user query
                for i in range(len(history) - 3, -1, -1):
                    msg = history[i]
                    if msg.get('type') == 'user' or msg.get('role') == 'user':
                        content = msg.get('content', msg.get('message', ''))
                        # Skip if this is field information or affirmative response
                        if not self.is_field_information_response(content, "") and not self.is_ticket_creation_request(content, ""):
                            original_query = content
                            break
            
            print(f"🔍 Original query identified: {original_query}")
            print(f"📋 Fields collected: {collected_fields}")
            
            # Try to create ticket with collected fields
            ticket_response = self.response_formatter.create_simulated_ticket(
                query=original_query or query,
                user_email=user_id,
                additional_description="User provided required field information",
                collected_fields=collected_fields
            )
            
            # Check if response is asking for more fields (field collection prompt)
            if "Additional Information Required" in ticket_response:
                # Still need more fields
                response_msg = f"📝 Thank you for the information! {ticket_response}"
            else:
                # Ticket was created successfully
                response_msg = ticket_response
            
            # Add to chat history
            self.chat_history_manager.add_message(user_id, "user", query)
            self.chat_history_manager.add_message(user_id, "assistant", response_msg)
            
            return {
                "query": query,
                "source": "FIELD_COLLECTION" if "Additional Information Required" in ticket_response else "TICKET_CREATION",
                "results_found": 1,
                "response": response_msg,
                "ticket_created": ticket_response if "Additional Information Required" not in ticket_response else None,
                "error": None,
                "chat_history": self.chat_history_manager.get_history(user_id)
            }
            
        except Exception as e:
            error_msg = f"Error processing field information: {e}"
            print(f"❌ {error_msg}")
            
            error_response = f"❌ Sorry, I had trouble processing your field information. Please try again or provide the information in this format:\n\nArea: [Your area]\nAffected Version: [Version number]\nReported Environment: [Environment name]"
            
            # Add to chat history
            self.chat_history_manager.add_message(user_id, "user", query)
            self.chat_history_manager.add_message(user_id, "assistant", error_response)
            
            return {
                "query": query,
                "source": "FIELD_COLLECTION_ERROR",
                "results_found": 0,
                "response": error_response,
                "ticket_created": None,
                "error": error_msg,
                "chat_history": self.chat_history_manager.get_history(user_id)
            }

    def process_ticket_creation_request(self, user_id: str, query: str, original_query: str = "") -> Dict[str, Any]:
        """
        Process a ticket creation request
        
        Args:
            user_id: User identifier (email)
            query: Current user query (could be "yes" or explicit ticket request)
            original_query: The original query that led to the ticket creation prompt
            
        Returns:
            Response with ticket creation results
        """
        try:
            print(f"🎫 Processing ticket creation request for user: {user_id}")
            # Determine the query to use for ticket creation
            ticket_query = ""
            additional_description = ""
            if original_query:
                ticket_query = original_query
                additional_description = "User requested ticket creation after search results were insufficient"
                print(f"📋 Using original query for ticket: {original_query}")
            else:
                query_lower = query.lower()
                explicit_requests = [
                    'create ticket', 'create a ticket', 'make ticket', 'make a ticket',
                    'submit ticket', 'submit a ticket', 'open ticket', 'open a ticket',
                    'file ticket', 'file a ticket', 'support ticket', 'log a ticket',
                    'raise a ticket', 'escalate to ticket'
                ]
                if any(req in query_lower for req in explicit_requests):
                    for req in explicit_requests:
                        if req in query_lower:
                            parts = query_lower.split(req)
                            if len(parts) > 1 and parts[1].strip():
                                ticket_query = parts[1].strip()
                                break
                            elif len(parts) > 0 and parts[0].strip():
                                ticket_query = parts[0].strip()
                                break
                    if not ticket_query or len(ticket_query) < 10:
                        history = self.chat_history_manager.get_history(user_id)
                        if history and len(history) > 1:
                            for msg in reversed(history[:-1]):
                                if msg.get('type') == 'user' or msg.get('role') == 'user':
                                    content = msg.get('content', msg.get('message', ''))
                                    if not self.is_ticket_creation_request(content, ""):
                                        ticket_query = content
                                        print(f"📋 Using recent query from history: {ticket_query}")
                                        break
                        if not ticket_query:
                            ticket_query = "Support assistance requested"
                            additional_description = "User explicitly requested ticket creation"
                    additional_description = "User explicitly requested ticket creation"
                else:
                    ticket_query = query
                    additional_description = "User requested ticket creation"
            print(f"🎯 Final ticket query: {ticket_query}")

            # Check if we're running in Streamlit mode
            if self.streamlit_mode:
                # For Streamlit, return a response that directly triggers the form
                ticket_prompt = f"🎫 **Creating Support Ticket**\n\n**Query:** {ticket_query}\n\nPlease fill out the ticket form below to complete your support request."
                
                # Store the query for potential ticket creation
                # Record messages in chat history
                self.chat_history_manager.add_message(user_id, "user", query)
                self.chat_history_manager.add_message(user_id, "assistant", ticket_prompt)
                
                return {
                    'response': ticket_prompt,
                    'formatted_response': ticket_prompt,
                    'ticket_creation_ready': True,
                    'original_query': ticket_query
                }

            # Use the enhanced TicketCreator for CLI mode
            ticket_creator = TicketCreator()
            
            ticket_data = ticket_creator.create_ticket(
                query=ticket_query,
                customer_email=user_id
            )
            
            ticket_response = f"✅ Ticket created successfully: {ticket_data.get('ticket_id', 'N/A')}"
            
            # Record messages in chat history
            self.chat_history_manager.add_message(user_id, "user", query)
            self.chat_history_manager.add_message(user_id, "assistant", ticket_response)

            return {
                "query": query,
                "source": "TICKET_CREATION",
                "results_found": 1,
                "response": ticket_response,
                "ticket_created": ticket_response,
                "error": None,
                "chat_history": self.chat_history_manager.get_history(user_id)
            }
            
        except Exception as e:
            error_msg = f"Error creating ticket: {e}"
            print(f"❌ {error_msg}")
            
            error_response = f"❌ Sorry, I encountered an error while creating your support ticket: {str(e)}"
            
            # Add to chat history
            self.chat_history_manager.add_message(user_id, "user", query)
            self.chat_history_manager.add_message(user_id, "assistant", error_response)
            
            return {
                "query": query,
                "source": "TICKET_CREATION_ERROR",
                "results_found": 0,
                "response": error_response,
                "ticket_created": None,
                "error": error_msg,
                "chat_history": self.chat_history_manager.get_history(user_id)
            }

    def process_query(self, user_id: str, query: str, history=None) -> Dict[str, Any]:
        """
        Process a user query through the LangGraph workflow, using chat history for context
        """
        print("🚀 Processing query:", query)
        
        # Check if this is a ticket creation request based on recent conversation
        previous_response = ""
        if history and len(history) > 0:
            # Get the last bot response to check for ticket creation prompts
            for msg in reversed(history):
                if msg.get('type') == 'bot' or msg.get('role') == 'assistant':
                    previous_response = msg.get('content', msg.get('message', ''))
                    break
        
        # Check if user is providing field information for ticket creation
        if self.is_field_information_response(query, previous_response):
            print("📝 Detected field information response")
            return self.process_field_information_response(user_id, query, history)
        
        # Check if user is responding to a ticket creation prompt
        if self.is_ticket_creation_request(query, previous_response):
            print("🎫 Detected ticket creation request")
            
            # Find the original query from history (the query that led to the ticket prompt)
            original_query = ""
            if history and len(history) >= 2:
                # Look for the user query that preceded the ticket creation prompt
                for i in range(len(history) - 2, -1, -1):
                    msg = history[i]
                    if msg.get('type') == 'user' or msg.get('role') == 'user':
                        content = msg.get('content', msg.get('message', ''))
                        # Skip if this is also an affirmative response
                        if not self.is_ticket_creation_request(content, ""):
                            original_query = content
                            break
            
            return self.process_ticket_creation_request(user_id, query, original_query)

        # Add user message to chat history
        self.chat_history_manager.add_message(user_id, "user", query)

        # Build context from history
        context = ""
        if history:
            context = "\n".join(
                f"{msg.get('role', msg.get('type', 'user'))}: {msg.get('message', msg.get('content', ''))}" for msg in history
            )

        initial_state: QueryState = {
            "query": query,
            "context": context,
            "user_email": user_id,  # Add user email to state for ticket creation
            "classified_source": None,
            "search_results": [],
            "similarity_scores": [],
            "formatted_response": None,
            "ticket_created": None,
            "error": None,
            "api_results": None
        }

        try:
            # Run the LangGraph workflow
            final_state_dict = self.graph.invoke(initial_state)

            formatted_response = final_state_dict.get('formatted_response')
            error = final_state_dict.get('error')

            print("\n📊 Processing complete")

            # Print the final response to console
            if formatted_response:
                print(formatted_response)

            if error:
                print(f"\n❌ Errors: {error}")

            # Add assistant response to chat history
            if formatted_response:
                self.chat_history_manager.add_message(user_id, "assistant", formatted_response)

            return {
                "query": final_state_dict.get('query'),
                "source": final_state_dict.get('classified_source'),
                "results_found": len(final_state_dict.get('search_results', [])),
                "response": formatted_response,
                "ticket_created": final_state_dict.get('ticket_created'),
                "ticket_creation_suggested": final_state_dict.get('ticket_creation_suggested', False),
                "error": error,
                "chat_history": self.chat_history_manager.get_history(user_id)
            }

        except Exception as e:
            error_msg = f"LangGraph execution error: {e}"
            print(f"\n❌ {error_msg}")
            return {
                "query": query,
                "source": None,
                "results_found": 0,
                "response": f"❌ System error: {e}",
                "ticket_created": None,
                "error": error_msg
            }

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        def safe_attr(obj, name, default="❌ Not Ready"):
            try:
                return getattr(obj, name)
            except Exception:
                return None

        # Safe checks to avoid attribute errors if tools are partially implemented
        def check_ready(obj, test_method_name="test_connection"):
            if obj is None:
                return "❌ Not Installed"
            try:
                method = getattr(obj, test_method_name, None)
                if callable(method):
                    ok = method()
                    return "✅ Ready" if ok else "❌ Connection Failed"
                # Fallback check for presence of any API client or property
                return "✅ Ready"
            except Exception:
                return "❌ Connection Failed"

        status = {
            "langgraph": "✅ Ready",
            "semantic_search": "✅ Ready",
            "response_formatter": "✅ Ready",
            "jira_tool": check_ready(self.jira_tool),
            "mindtouch_tool": check_ready(self.mindtouch_tool)
        }

        # Check vector store status
        for source in ["JIRA", "MINDTOUCH"]:
            try:
                doc_count = self.semantic_search.get_stored_document_count(source)
                status[f"{source.lower()}_documents"] = f"{doc_count} documents stored"
            except Exception:
                status[f"{source.lower()}_documents"] = "Unknown"

        return status


def main():
    """Main function"""
    processor = IntelligentQueryProcessor()

    print("🚀 Intelligent Query Processor")

    # Show system status
    status = processor.get_system_status()
    print("📊 System Status:")
    for component, state in status.items():
        print(f"   {component}: {state}")
    print()

    while True:
        try:
            query = input("💬 Enter your query (or 'quit' to exit): ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                print("Please enter a valid query.")
                continue

            # Process the query through LangGraph
            # You need a user_id for each session/user. For demo, use a test email
            user_id = "abc@wdc.com"  # Test email for WDC customer
            result = processor.process_query(user_id, query)
            
            # Check if ticket creation was suggested and handle user response
            if result.get('ticket_creation_suggested', False):
                print("\n💡 The system has suggested creating a support ticket.")
                follow_up = input("💬 Would you like to create a ticket? (yes/no): ").strip().lower()
                
                if follow_up in ['yes', 'y', 'create ticket', 'ticket']:
                    print("🎫 Proceeding with ticket creation...")
                    # Get the original query from chat history for ticket creation
                    history = processor.chat_history_manager.get_history(user_id)
                    original_query = query
                    if history and len(history) >= 2:
                        for msg in reversed(history[:-1]):  # Skip the last message (current response)
                            if msg.get('type') == 'user' or msg.get('role') == 'user':
                                original_query = msg.get('content', msg.get('message', query))
                                break
                    
                    # Process ticket creation
                    ticket_result = processor.process_ticket_creation_request(user_id, "yes", original_query)
                    print(ticket_result.get('response', 'Ticket creation completed.'))
                else:
                    print("👍 No problem! Let me know if you need anything else.")
            
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


# Create an alias for backwards compatibility
nQuiry = IntelligentQueryProcessor


if __name__ == "__main__":
    main()
