"""
nQuiry - Intelligent Query Processing System
New Flow: JIRA (organization-specific) → MindTouch → Create Ticket
"""

from typing import Dict, List, Any, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from semantic_search import SemanticSearch
from response_formatter import ResponseFormatter
from ticket_creator import TicketCreator
from tools.mindtouch_tool import MindTouchTool
from tools.jira_tool import JiraTool
from chat_history_manager import ChatHistoryManager

# Configuration
FALLBACK_SEARCH_ENABLED = False  # Disabled - relying on new flow


class QueryState(TypedDict):
    """State model for the LangGraph workflow"""
    query: str
    context: Optional[str]
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

    def __init__(self):
        # Initialize basic components
        self.semantic_search = SemanticSearch()
        self.response_formatter = ResponseFormatter()
        self.ticket_creator = TicketCreator()
        self.chat_history_manager = ChatHistoryManager()

        # Get customer email upfront for all queries (required for customer identification)
        print("🔐 Customer Authentication Required")
        print("=" * 40)
        print("💡 Please provide your email for customer identification and role-based access")
        customer_email = MindTouchTool.get_customer_email_from_input()

        # Initialize all tools
        self.jira_tool = JiraTool()
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
        print(f"🔄 New Flow: JIRA ({org}) → MindTouch → Create Ticket")

        # Initialize the LangGraph
        self.graph = self._build_langgraph()

    def _build_langgraph(self):
        """Build the LangGraph workflow with new routing: JIRA -> MindTouch -> Create Ticket"""

        workflow = StateGraph(dict)

        # Add nodes for the simplified flow
        workflow.add_node("search_jira", self.search_jira_node)
        workflow.add_node("search_mindtouch", self.search_mindtouch_node)
        workflow.add_node("format_response", self.format_response_node)
        workflow.add_node("create_ticket", self.create_ticket_node)

        # Define the new routing logic
        def should_fallback_to_mindtouch(state) -> str:
            """Fallback to MindTouch if JIRA search yields no results"""
            search_results = state.get('search_results', [])
            
            if not search_results:
                print("📖 No JIRA results found - fallback to MindTouch")
                return "search_mindtouch"
            else:
                print("� JIRA results found - formatting response")
                return "format_response"

        def should_create_ticket_or_format(state) -> str:
            """Decide whether to create ticket or format response"""
            search_results = state.get('search_results', [])

            if not search_results:
                print("🎫 No results found anywhere - creating ticket")
                return "create_ticket"
            else:
                print("📝 Results found - formatting response")
                return "format_response"

        # Define edges for simplified sequential flow
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
                "create_ticket": "create_ticket",
                "format_response": "format_response"
            }
        )
        
        workflow.add_edge("format_response", END)
        workflow.add_edge("create_ticket", END)

        return workflow.compile()

    def search_jira_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Search JIRA for organization-specific tickets and rank results"""
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
                ranked_docs, scores = self.semantic_search.search_documents(documents, query)
                
                state['search_results'] = ranked_docs
                state['similarity_scores'] = scores
                print(f"✅ Ranked {len(ranked_docs)} JIRA results")
                
                # Display brief summary of top results
                for i, doc in enumerate(ranked_docs[:3]):
                    print(f"   {i+1}. {doc.get('key', 'Unknown')}: {doc.get('title', 'No title')[:60]}...")
                    
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

            # Get MindTouch documents - this returns formatted LLM response
            documents = self.mindtouch_tool.search_pages(query, limit=20)
            
            if documents:
                print(f"📊 MindTouch search completed: {len(documents)} pages")
                
                # MindTouch returns already processed/formatted documents
                # No additional semantic search needed since MindTouch uses LLM completion
                state['search_results'] = documents
                state['similarity_scores'] = [1.0] * len(documents)  # All results are relevant
                
                print(f"✅ MindTouch results ready for formatting")
            else:
                state['search_results'] = []
                state['similarity_scores'] = []
                print("⚠️  No MindTouch pages found")

        except Exception as e:
            print(f"❌ Error searching MindTouch: {e}")
            state['error'] = f"MindTouch search error: {e}"
            state['search_results'] = []
            state['similarity_scores'] = []

        return state

    def format_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Format the search results"""
        try:
            print("✍️  Formatting response...")

            search_results = state.get('search_results', [])
            similarity_scores = state.get('similarity_scores', [])
            
            # Determine source based on current workflow stage
            # Since we have a sequential flow, we can track which search was last executed
            if search_results:
                # Check if results have JIRA-specific fields to identify source
                first_result = search_results[0] if isinstance(search_results, list) and search_results else {}
                if isinstance(first_result, dict) and first_result.get('key') and 'PROJ-' in str(first_result.get('key', '')):
                    source = 'JIRA'
                else:
                    source = 'MINDTOUCH'
            else:
                source = 'UNKNOWN'

            results_with_scores = list(zip(search_results, similarity_scores)) if similarity_scores else [(result, 1.0) for result in search_results]
            formatted_response = self.response_formatter.format_search_results(
                query=state.get('query', ''),
                results=results_with_scores,
                source=source,
                context=state.get('context', '')
            )

            state['formatted_response'] = formatted_response
            print(f"✅ Response formatted successfully from {source}")

        except Exception as e:
            print(f"❌ Error formatting response: {e}")
            state['error'] = f"Response formatting error: {e}"
            state['formatted_response'] = f"Error formatting response: {e}"

        return state

    def create_ticket_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph Node: Create support ticket using custom JIRA tool"""
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
                results_with_scores = list(zip(search_results, similarity_scores))
                formatted_results = self.response_formatter.format_search_results(
                    query=state.get('query', ''),
                    results=results_with_scores,
                    source=source
                )
                print(formatted_results)

            # Ask user if they want to create a new ticket
            print("\n🎫 Would you like to create a new JIRA ticket for this query?")
            create_ticket = input("Create ticket? (y/n): ").strip().lower()

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
                    results_with_scores = list(zip(search_results, similarity_scores))
                    state['formatted_response'] = self.response_formatter.format_search_results(
                        query=state.get('query', ''),
                        results=results_with_scores,
                        source=state.get('classified_source', '')
                    )
                else:
                    state['formatted_response'] = "✅ No new ticket created. No relevant existing issues found."

        except Exception as e:
            print(f"❌ Error in ticket creation process: {e}")
            state['error'] = f"Ticket creation error: {e}"
            state['formatted_response'] = f"❌ Error in ticket creation process: {e}"

        return state

    def process_query(self, user_id: str, query: str, history=None) -> Dict[str, Any]:
        """
        Process a user query through the LangGraph workflow, using chat history for context
        """
        print("🚀 Processing query:", query)

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
            # You need a user_id for each session/user. For demo, use a static string or prompt for it.
            user_id = "demo_user"  # Replace with actual user identifier in production
            result = processor.process_query(user_id, query)
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
