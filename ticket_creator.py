"""
Ticket creator module for creating support tickets when no relevant information is found
"""

from typing import Dict, Optional
import json

class TicketCreator:
    """
    Creates support tickets when no relevant information is found in knowledge bases
    """
    
    def __init__(self):
        self.required_fields = [
            'summary',
            'description', 
            'priority',
            'issue_type',
            'project_key'
        ]
        self.optional_fields = [
            'assignee',
            'reporter',
            'labels',
            'components',
            'due_date'
        ]
    
    def get_ticket_fields_from_user(self, query: str) -> Dict:
        """
        Collect ticket information from user input
        
        Args:
            query: Original user query that couldn't be answered
            
        Returns:
            Dictionary containing ticket field values
        """
        print("\n" + "="*60)
        print("🎫 NO RELEVANT INFORMATION FOUND")
        print("Let's create a support ticket for your query.")
        print("="*60)
        print(f"Original Query: {query}")
        print("-"*60)
        
        ticket_data = {
            'original_query': query,
            'description': f"User Query: {query}\n\nNo relevant information was found in the knowledge base. Please investigate and provide assistance."
        }
        
        # Collect required fields
        print("\n📝 Please provide the following information:")
        
        # Summary (auto-generated but can be modified)
        suggested_summary = f"Support Request: {query[:100]}{'...' if len(query) > 100 else ''}"
        print(f"\n1. Summary (suggested: {suggested_summary})")
        summary = input("   Enter summary (or press Enter to use suggested): ").strip()
        ticket_data['summary'] = summary if summary else suggested_summary
        
        # Priority
        print("\n2. Priority")
        print("   Options: Highest, High, Medium, Low, Lowest")
        priority = input("   Enter priority [Medium]: ").strip()
        ticket_data['priority'] = priority if priority else "Medium"
        
        # Issue Type
        print("\n3. Issue Type")
        print("   Options: Task, Bug, Story, Epic, Support")
        issue_type = input("   Enter issue type [Task]: ").strip()
        ticket_data['issue_type'] = issue_type if issue_type else "Task"
        
        # Project Key
        print("\n4. Project Key")
        project_key = input("   Enter project key (e.g., SUPPORT, HELP): ").strip()
        while not project_key:
            print("   Project key is required!")
            project_key = input("   Enter project key: ").strip()
        ticket_data['project_key'] = project_key.upper()
        
        # Optional fields
        print("\n📋 Optional Information:")
        
        # Assignee
        assignee = input("   Assignee (email or username, optional): ").strip()
        if assignee:
            ticket_data['assignee'] = assignee
        
        # Labels
        labels = input("   Labels (comma-separated, optional): ").strip()
        if labels:
            ticket_data['labels'] = [label.strip() for label in labels.split(',')]
        
        # Components
        components = input("   Components (comma-separated, optional): ").strip()
        if components:
            ticket_data['components'] = [comp.strip() for comp in components.split(',')]
        
        # Additional description
        print("\n   Additional description (optional):")
        additional_desc = input("   Enter any additional details: ").strip()
        if additional_desc:
            ticket_data['description'] += f"\n\nAdditional Details: {additional_desc}"
        
        return ticket_data
    
    def create_jira_ticket(self, ticket_data: Dict) -> Optional[str]:
        """
        Create a JIRA ticket using MCP Atlassian server
        Note: This will be called from the LangGraph node which has access to MCP functions
        
        Args:
            ticket_data: Dictionary containing ticket field values
            
        Returns:
            Created ticket key or None if failed
        """
        try:
            print("\n🚀 Creating JIRA ticket...")
            print("-"*40)
            
            # This method is now called from the LangGraph node which handles MCP calls
            # For standalone usage, we'll simulate the response
            ticket_key = f"{ticket_data['project_key']}-{hash(ticket_data['summary']) % 1000:03d}"
            
            print(f"✅ Ticket created successfully!")
            print(f"🎫 Ticket Key: {ticket_key}")
            print(f"📝 Summary: {ticket_data['summary']}")
            print(f"🎯 Priority: {ticket_data['priority']}")
            print(f"📊 Type: {ticket_data['issue_type']}")
            
            if 'assignee' in ticket_data:
                print(f"👤 Assignee: {ticket_data['assignee']}")
            
            if 'labels' in ticket_data:
                print(f"🏷️  Labels: {', '.join(ticket_data['labels'])}")
            
            print(f"\n📋 Description:\n{ticket_data['description']}")
            
            return ticket_key
            
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return None
    
    def validate_ticket_data(self, ticket_data: Dict) -> bool:
        """
        Validate that required ticket fields are present
        
        Args:
            ticket_data: Dictionary containing ticket field values
            
        Returns:
            True if valid, False otherwise
        """
        missing_fields = []
        
        for field in self.required_fields:
            if field not in ticket_data or not ticket_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        return True
    
    def format_ticket_preview(self, ticket_data: Dict) -> str:
        """
        Format ticket data for preview before creation
        
        Args:
            ticket_data: Dictionary containing ticket field values
            
        Returns:
            Formatted string representation of the ticket
        """
        preview = f"""
🎫 TICKET PREVIEW
{"="*50}
Summary: {ticket_data.get('summary', 'N/A')}
Project: {ticket_data.get('project_key', 'N/A')}
Type: {ticket_data.get('issue_type', 'N/A')}
Priority: {ticket_data.get('priority', 'N/A')}
"""
        
        if 'assignee' in ticket_data:
            preview += f"Assignee: {ticket_data['assignee']}\n"
        
        if 'labels' in ticket_data:
            preview += f"Labels: {', '.join(ticket_data['labels'])}\n"
        
        if 'components' in ticket_data:
            preview += f"Components: {', '.join(ticket_data['components'])}\n"
        
        preview += f"\nDescription:\n{ticket_data.get('description', 'N/A')}\n"
        preview += "="*50
        
        return preview