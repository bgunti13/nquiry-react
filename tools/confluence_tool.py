"""
Confluence REST API Tool for accessing Confluence instances
"""

import os
import requests
import json
from typing import List, Dict, Any, Optional
from requests.auth import HTTPBasicAuth
import html2text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConfluenceTool:
    """Tool for interacting with Confluence REST API"""
    
    def __init__(self):
        """Initialize Confluence tool with configuration from environment"""
        # Try different environment variable names for compatibility
        self.base_url = (
            os.getenv('CONFLUENCE_URL') or 
            os.getenv('CONFLUENCE_BASE_URL')
        )
        self.username = (
            os.getenv('CONFLUENCE_USERNAME') or 
            os.getenv('CONFLUENCE_USER')
        )
        self.api_token = (
            os.getenv('CONFLUENCE_API_TOKEN') or 
            os.getenv('CONFLUENCE_TOKEN')
        )
        
        if not all([self.base_url, self.username, self.api_token]):
            print("⚠️  Confluence configuration incomplete.")
            print(f"   CONFLUENCE_URL: {'✅' if self.base_url else '❌'}")
            print(f"   CONFLUENCE_USERNAME: {'✅' if self.username else '❌'}")
            print(f"   CONFLUENCE_API_TOKEN: {'✅' if self.api_token else '❌'}")
        
        # Ensure base_url ends with /rest/api/
        if self.base_url:
            # Remove /wiki suffix if present (from MCP format)
            if self.base_url.endswith('/wiki'):
                self.base_url = self.base_url[:-5]
            
            if not self.base_url.endswith('/'):
                self.base_url += '/'
            if not self.base_url.endswith('rest/api/'):
                if not self.base_url.endswith('rest/api'):
                    self.base_url += 'rest/api/'
        
        self.session = requests.Session()
        if self.username and self.api_token:
            self.session.auth = HTTPBasicAuth(self.username, self.api_token)
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Initialize HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
    
    def test_connection(self) -> bool:
        """Test connection to Confluence API"""
        try:
            if not all([self.base_url, self.username, self.api_token]):
                return False
            
            response = self.session.get(f"{self.base_url}user/current")
            return response.status_code == 200
        except Exception as e:
            print(f"Confluence connection test failed: {e}")
            return False
    
    def search_pages(self, query: str, limit: int = 20, space_key: str = None) -> List[Dict[str, Any]]:
        """
        Search Confluence pages
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            space_key: Optional space key to limit search
            
        Returns:
            List of Confluence pages
        """
        try:
            if not self.test_connection():
                print("❌ Confluence connection not available")
                return []

            # Use siteSearch for better content matching
            cql_query = f'siteSearch ~ "{query}"'
            if space_key:
                cql_query += f' AND space = "{space_key}"'
            
            print(f"🔍 Confluence CQL: {cql_query}")
            print(f"📡 Confluence URL: {self.base_url}content/search")

            # Prepare search parameters
            params = {
                'cql': cql_query,
                'limit': limit,
                'expand': 'body.storage,space,version,history'
            }

            response = self.session.get(
                f"{self.base_url}content/search",
                params=params
            )
            
            print(f"📊 Confluence Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📄 Raw results count: {len(data.get('results', []))}")
                pages = []
                
                for page in data.get('results', []):
                    # Get page content
                    content_html = ''
                    if page.get('body') and page.get('body').get('storage'):
                        content_html = page['body']['storage'].get('value', '')
                    
                    # Convert HTML to text
                    content_text = self.html_converter.handle(content_html) if content_html else ''
                    
                    # Extract page data
                    page_data = {
                        'id': page.get('id', ''),
                        'title': page.get('title', ''),
                        'content': content_text,
                        'space': page.get('space', {}).get('key', '') if page.get('space') else '',
                        'space_name': page.get('space', {}).get('name', '') if page.get('space') else '',
                        'url': f"{self.base_url.replace('/rest/api/', '')}{page.get('_links', {}).get('webui', '')}" if page.get('_links') else '',
                        'created': page.get('history', {}).get('createdDate', '') if page.get('history') else '',
                        'updated': page.get('version', {}).get('when', '') if page.get('version') else '',
                        'creator': page.get('history', {}).get('createdBy', {}).get('displayName', '') if page.get('history', {}).get('createdBy') else '',
                        'version': page.get('version', {}).get('number', 1) if page.get('version') else 1,
                        'type': page.get('type', 'page')
                    }
                    
                    pages.append(page_data)
                
                print(f"✅ Found {len(pages)} Confluence pages")
                return pages
            else:
                print(f"❌ Confluence search failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching Confluence: {e}")
            return []
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific Confluence page by ID
        
        Args:
            page_id: Confluence page ID
            
        Returns:
            Page details or None if not found
        """
        try:
            if not self.test_connection():
                print("❌ Confluence connection not available")
                return None
            
            params = {
                'expand': 'body.storage,space,version,history,children.page'
            }
            
            response = self.session.get(f"{self.base_url}content/{page_id}", params=params)
            
            if response.status_code == 200:
                page = response.json()
                
                # Get page content
                content_html = ''
                if page.get('body') and page.get('body').get('storage'):
                    content_html = page['body']['storage'].get('value', '')
                
                # Convert HTML to text
                content_text = self.html_converter.handle(content_html) if content_html else ''
                
                return {
                    'id': page.get('id', ''),
                    'title': page.get('title', ''),
                    'content': content_text,
                    'space': page.get('space', {}).get('key', '') if page.get('space') else '',
                    'space_name': page.get('space', {}).get('name', '') if page.get('space') else '',
                    'url': f"{self.base_url.replace('/rest/api/', '')}{page.get('_links', {}).get('webui', '')}" if page.get('_links') else '',
                    'created': page.get('history', {}).get('createdDate', '') if page.get('history') else '',
                    'updated': page.get('version', {}).get('when', '') if page.get('version') else '',
                    'creator': page.get('history', {}).get('createdBy', {}).get('displayName', '') if page.get('history', {}).get('createdBy') else '',
                    'version': page.get('version', {}).get('number', 1) if page.get('version') else 1,
                    'type': page.get('type', 'page')
                }
            else:
                print(f"❌ Failed to get Confluence page {page_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting Confluence page: {e}")
            return None
    
    def create_page(self, space_key: str, title: str, content: str, 
                   parent_id: str = None) -> Optional[str]:
        """
        Create a new Confluence page
        
        Args:
            space_key: Confluence space key
            title: Page title
            content: Page content (in Confluence storage format)
            parent_id: Optional parent page ID
            
        Returns:
            Created page ID or None if failed
        """
        try:
            if not self.test_connection():
                print("❌ Confluence connection not available")
                return None
            
            payload = {
                "type": "page",
                "title": title,
                "space": {"key": space_key},
                "body": {
                    "storage": {
                        "value": content,
                        "representation": "storage"
                    }
                }
            }
            
            if parent_id:
                payload["ancestors"] = [{"id": parent_id}]
            
            response = self.session.post(
                f"{self.base_url}content",
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                created_page = response.json()
                page_id = created_page.get('id')
                print(f"✅ Created Confluence page: {page_id}")
                return page_id
            else:
                print(f"❌ Failed to create Confluence page: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating Confluence page: {e}")
            return None
    
    def get_spaces(self) -> List[Dict[str, Any]]:
        """Get list of available Confluence spaces"""
        try:
            if not self.test_connection():
                return []
            
            params = {
                'limit': 100,
                'expand': 'description'
            }
            
            response = self.session.get(f"{self.base_url}space", params=params)
            
            if response.status_code == 200:
                data = response.json()
                spaces = []
                
                for space in data.get('results', []):
                    space_data = {
                        'key': space.get('key', ''),
                        'name': space.get('name', ''),
                        'description': space.get('description', {}).get('plain', {}).get('value', '') if space.get('description', {}).get('plain') else '',
                        'type': space.get('type', ''),
                        'url': f"{self.base_url.replace('/rest/api/', '')}{space.get('_links', {}).get('webui', '')}" if space.get('_links') else ''
                    }
                    spaces.append(space_data)
                
                return spaces
            else:
                print(f"❌ Failed to get Confluence spaces: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting Confluence spaces: {e}")
            return []
    
    def search_by_space(self, space_keys: List[str], query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search Confluence pages within specific spaces
        
        Args:
            space_keys: List of space keys to search in
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of Confluence pages
        """
        all_results = []
        
        for space_key in space_keys:
            results = self.search_pages(query, limit // len(space_keys), space_key)
            all_results.extend(results)
        
        # Sort by relevance/updated date
        all_results.sort(key=lambda x: x.get('updated', ''), reverse=True)
        
        return all_results[:limit]