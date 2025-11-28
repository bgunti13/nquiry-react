"""
Zendesk API Tool for nQuiry Integration
Provides ticket search and creation capabilities for Zendesk
"""

import requests
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ZendeskTool:
    """
    Tool for interacting with Zendesk API for ticket search and creation
    """
    
    def __init__(self):
        # Load Zendesk configuration from environment variables
        self.api_token = os.getenv('ZENDESK_API_TOKEN')
        self.subdomain = os.getenv('ZENDESK_SUBDOMAIN')
        self.user_email = os.getenv('ZENDESK_USER_EMAIL')
        
        if not all([self.api_token, self.subdomain, self.user_email]):
            raise ValueError("Missing Zendesk configuration. Please set ZENDESK_API_TOKEN, ZENDESK_SUBDOMAIN, and ZENDESK_USER_EMAIL")
        
        self.base_url = f'https://{self.subdomain}.zendesk.com/api/v2'
        self.auth = (f'{self.user_email}/token', self.api_token)
        
        print(f"✅ Zendesk tool initialized for subdomain: {self.subdomain}")
    
    def test_connection(self) -> bool:
        """
        Test Zendesk API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(f'{self.base_url}/users/me.json', auth=self.auth)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Zendesk connection failed: {e}")
            return False
    
    def search_tickets(self, query: str, organization: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search Zendesk tickets based on query and optional organization filter
        
        Args:
            query: Search query
            organization: Optional organization name to filter by
            limit: Maximum number of tickets to return
            
        Returns:
            List of ticket dictionaries
        """
        try:
            # For semantic search, we want to get a broader set of tickets
            # and let the semantic ranking determine relevance
            if query and query.strip():
                # Get recent tickets that might be relevant - cast a wider net
                # We'll rely on semantic search for ranking, not keyword matching
                search_query = 'type:ticket status>new'
            else:
                # If no query, get recent tickets
                search_query = 'type:ticket'
            
            if organization:
                # Add organization filter if provided
                search_query += f' organization:"{organization}"'
            
            # Add recent tickets filter - get more recent tickets for better semantic matching
            search_query += ' sort:updated_at order:desc'
            
            print(f"🔍 Searching Zendesk tickets with query: {search_query}")
            print(f"📝 Will use semantic search to rank by relevance for: '{query}'")
            
            # Make API request - get more tickets for semantic analysis
            params = {
                'query': search_query,
                'per_page': min(limit * 3, 100)  # Get 3x more tickets for semantic ranking
            }
            
            response = requests.get(
                f'{self.base_url}/search.json',
                params=params,
                auth=self.auth
            )
            
            if response.status_code == 200:
                data = response.json()
                tickets = []
                
                for result in data.get('results', []):
                    if result.get('result_type') == 'ticket':
                        ticket = self._format_ticket(result)
                        tickets.append(ticket)
                
                print(f"✅ Found {len(tickets)} Zendesk tickets")
                return tickets
            else:
                print(f"❌ Zendesk search failed with status {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching Zendesk tickets: {e}")
            return []
    
    def search_tickets_by_organization(self, query: str, organization: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search Zendesk tickets for a specific organization
        
        Args:
            query: Search query
            organization: Organization name to filter by
            limit: Maximum number of tickets to return
            
        Returns:
            List of ticket dictionaries with organization match info
        """
        tickets = self.search_tickets(query, organization, limit)
        
        # Add organization match information
        for ticket in tickets:
            ticket['organization_match'] = organization
        
        return tickets
    
    def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Zendesk ticket
        
        Args:
            ticket_data: Dictionary containing ticket information
            
        Returns:
            Created ticket information or error details
        """
        try:
            # Prepare ticket payload
            payload = {
                "ticket": {
                    "subject": ticket_data.get('summary', 'Support Request'),
                    "comment": {
                        "body": ticket_data.get('description', 'No description provided')
                    },
                    "priority": self._map_priority(ticket_data.get('priority', 'normal')),
                    "type": ticket_data.get('type', 'question'),
                    "status": "open"
                }
            }
            
            # Add optional fields if provided
            if ticket_data.get('assignee'):
                payload["ticket"]["assignee_email"] = ticket_data['assignee']
            
            if ticket_data.get('tags'):
                payload["ticket"]["tags"] = ticket_data['tags'] if isinstance(ticket_data['tags'], list) else [ticket_data['tags']]
            
            print(f"🎫 Creating Zendesk ticket: {payload['ticket']['subject']}")
            
            response = requests.post(
                f'{self.base_url}/tickets.json',
                json=payload,
                auth=self.auth,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                ticket = response.json()['ticket']
                ticket_id = ticket['id']
                ticket_url = f"https://{self.subdomain}.zendesk.com/agent/tickets/{ticket_id}"
                
                print(f"✅ Zendesk ticket created successfully: #{ticket_id}")
                
                return {
                    'status': 'success',
                    'ticket_id': ticket_id,
                    'ticket_key': f"ZD-{ticket_id}",
                    'ticket_url': ticket_url,
                    'subject': ticket['subject'],
                    'created_date': ticket['created_at']
                }
            else:
                print(f"❌ Failed to create Zendesk ticket. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return {
                    'status': 'error',
                    'message': f"Failed to create ticket: {response.text}"
                }
                
        except Exception as e:
            print(f"❌ Error creating Zendesk ticket: {e}")
            return {
                'status': 'error',
                'message': f"Error creating ticket: {str(e)}"
            }
    
    def _format_ticket(self, raw_ticket: Dict) -> Dict[str, Any]:
        """
        Format raw Zendesk ticket data into standardized format
        
        Args:
            raw_ticket: Raw ticket data from Zendesk API
            
        Returns:
            Formatted ticket dictionary
        """
        return {
            'key': f"ZD-{raw_ticket.get('id', '')}",
            'id': raw_ticket.get('id'),
            'summary': raw_ticket.get('subject', ''),
            'content': raw_ticket.get('description', ''),
            'status': raw_ticket.get('status', ''),
            'priority': raw_ticket.get('priority', ''),
            'assignee': raw_ticket.get('assignee_id', ''),
            'created': raw_ticket.get('created_at', ''),
            'updated': raw_ticket.get('updated_at', ''),
            'labels': raw_ticket.get('tags', []),
            'type': raw_ticket.get('type', ''),
            'url': raw_ticket.get('url', ''),
            'organization': raw_ticket.get('organization_id', ''),
            'platform': 'Zendesk'
        }
    
    def _map_priority(self, priority: str) -> str:
        """
        Map generic priority to Zendesk priority values
        
        Args:
            priority: Generic priority string
            
        Returns:
            Zendesk priority value
        """
        priority_mapping = {
            'lowest': 'low',
            'low': 'low',
            'medium': 'normal',
            'normal': 'normal',
            'high': 'high',
            'highest': 'urgent',
            'critical': 'urgent',
            'urgent': 'urgent'
        }
        
        return priority_mapping.get(priority.lower(), 'normal')
    
    def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get list of organizations in Zendesk
        
        Returns:
            List of organization dictionaries
        """
        try:
            response = requests.get(f'{self.base_url}/organizations.json', auth=self.auth)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('organizations', [])
            else:
                print(f"❌ Failed to get organizations: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting organizations: {e}")
            return []


# Integration function for nquiry main workflow
def search_zendesk_tickets(query: str, organization: str = None) -> Dict[str, Any]:
    """
    Integration function for searching Zendesk tickets
    
    Args:
        query: Search query
        organization: Optional organization filter
        
    Returns:
        Search results in standardized format
    """
    try:
        zendesk_tool = ZendeskTool()
        
        if not zendesk_tool.test_connection():
            return {
                'status': 'error',
                'message': 'Failed to connect to Zendesk'
            }
        
        tickets = zendesk_tool.search_tickets(query, organization)
        
        return {
            'status': 'success',
            'source': 'Zendesk',
            'results': tickets,
            'count': len(tickets)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Zendesk search error: {str(e)}'
        }


def create_zendesk_ticket(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integration function for creating Zendesk tickets
    
    Args:
        ticket_data: Ticket information dictionary
        
    Returns:
        Ticket creation result
    """
    try:
        zendesk_tool = ZendeskTool()
        
        if not zendesk_tool.test_connection():
            return {
                'status': 'error',
                'message': 'Failed to connect to Zendesk'
            }
        
        return zendesk_tool.create_ticket(ticket_data)
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Zendesk ticket creation error: {str(e)}'
        }


if __name__ == "__main__":
    # Test the tool
    tool = ZendeskTool()
    
    if tool.test_connection():
        print("✅ Zendesk connection successful")
        
        # Test search
        results = tool.search_tickets("login issue", limit=5)
        print(f"Found {len(results)} tickets")
        
        # Test organizations
        orgs = tool.get_organizations()
        print(f"Found {len(orgs)} organizations")
        
    else:
        print("❌ Zendesk connection failed")