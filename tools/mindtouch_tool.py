"""
MindTouch API tool for LLM-based query responses with role-based content filtering
"""

import hashlib
import time
import requests
import hmac
import urllib.parse
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from config import MINDTOUCH_API_KEY, MINDTOUCH_API_SECRET, MINDTOUCH_USERNAME

# Import the dynamic customer role manager
try:
    from customer_role_manager import customer_role_manager
    DYNAMIC_MAPPING_AVAILABLE = True
except ImportError:
    print("⚠️  Dynamic customer mapping not available, using fallback")
    DYNAMIC_MAPPING_AVAILABLE = False

class MindTouchTool:
    """
    Tool for interacting with MindTouch LLM completion API with role-based content filtering
    """
    
    def __init__(self, customer_email: str = None, user_role: str = None):
        self.api_key = MINDTOUCH_API_KEY
        self.api_secret = MINDTOUCH_API_SECRET
        
        # Detect customer organization and role from email
        if customer_email:
            self.customer_email = customer_email
            self.customer_org_info = self._detect_customer_organization(customer_email)
            self.user_role = self.customer_org_info.get('primary_role', '=customer')
            print(f"🏢 Detected Organization: {self.customer_org_info.get('organization', 'Unknown')}")
            print(f"🎭 Assigned MindTouch Role: {self.user_role}")
        else:
            # Fallback to provided role or config default
            self.customer_email = None
            self.customer_org_info = {}
            self.user_role = user_role or MINDTOUCH_USERNAME
            print(f"⚠️  No customer email provided, using default role: {self.user_role}")
        
        print(f"🔧 MindTouch initialized with role: {self.user_role}")
    
    def _detect_customer_organization(self, email: str) -> Dict:
        """
        Detect customer organization from email domain using dynamic mappings
        
        Args:
            email: Customer email address
            
        Returns:
            Dictionary with organization info and roles
        """
        if not email or '@' not in email:
            print(f"⚠️  Invalid email format: {email}")
            return {'organization': 'Unknown', 'primary_role': '=customer', 'roles': ['=customer']}
        
        domain = email.split('@')[1].lower()
        
        # Use dynamic mapping if available
        if DYNAMIC_MAPPING_AVAILABLE:
            org_info = customer_role_manager.get_customer_mapping(domain)
            if org_info:
                print(f"✅ Found organization mapping for domain: {domain}")
                return org_info
        
        # Fallback for unknown domains
        print(f"❌ No organization mapping found for domain: {domain}")
        if DYNAMIC_MAPPING_AVAILABLE:
            # Show available domains from Excel
            all_mappings = customer_role_manager.get_all_mappings()
            sample_domains = list(all_mappings.keys())[:5]
            print(f"💡 Sample available domains: {sample_domains}")
        
        return {
            'organization': domain.upper(), 
            'primary_role': '=customer',
            'roles': ['=customer']
        }
    
    @staticmethod
    def get_customer_email_from_input() -> str:
        """
        Get customer email from terminal input
        
        Returns:
            Customer email address
        """
        print("\n🔐 MindTouch Customer Authentication")
        print("=" * 40)
        
        while True:
            email = input("📧 Enter customer email: ").strip().lower()
            
            if not email:
                print("❌ Email cannot be empty. Please try again.")
                continue
            
            if '@' not in email:
                print("❌ Invalid email format. Please include @ symbol.")
                continue
            
            # Show available test accounts from dynamic mappings
            if DYNAMIC_MAPPING_AVAILABLE:
                all_mappings = customer_role_manager.get_all_mappings()
                sample_domains = list(all_mappings.keys())[:5]
                print(f"💡 Test accounts available: {', '.join([f'test@{domain}' for domain in sample_domains])}")
            else:
                print("💡 Dynamic mapping not available - using fallback")
            
            return email
    
    def get_customer_info(self) -> Dict:
        """
        Get current customer information
        
        Returns:
            Dictionary with customer details
        """
        return {
            'email': self.customer_email,
            'organization': self.customer_org_info.get('organization', 'Unknown'),
            'role': self.user_role,
            'available_roles': self.customer_org_info.get('roles', []),
            'domain': self.customer_email.split('@')[1] if self.customer_email else None,
            'dynamic_mapping': DYNAMIC_MAPPING_AVAILABLE
        }
    
    def get_mapping_stats(self) -> Dict:
        """
        Get statistics about available customer mappings
        
        Returns:
            Dictionary with mapping statistics
        """
        if DYNAMIC_MAPPING_AVAILABLE:
            return customer_role_manager.get_mapping_stats()
        else:
            return {
                'total_customers': 0,
                'role_distribution': {},
                'last_loaded': 'Not available',
                'excel_file': 'Not configured',
                'file_exists': False,
                'dynamic_mapping': False
            }
    
    def set_user_role(self, role: str):
        """
        Set user role for content filtering
        
        Args:
            role: User role (e.g., '=GoS-HT', '=GoS-LS', '=customer')
        """
        self.user_role = role
        print(f"🔄 MindTouch role updated to: {self.user_role}")
    
    def _generate_auth_token(self) -> str:
        """
        Generate HMAC-based authentication token for MindTouch API
        
        Returns:
            Authentication token string
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("MindTouch API key and secret are required")
        
        # Generate timestamp
        epoch = str(int(time.time()))
        
        # Create message for HMAC: key_timestamp_user
        message_bytes = f'{self.api_key}_{epoch}_{self.user_role}'.encode('utf-8')
        secret_bytes = self.api_secret.encode('utf-8')
        
        # Generate HMAC-SHA256 hash
        hash_value = hmac.new(secret_bytes, message_bytes, digestmod=hashlib.sha256).hexdigest().lower()
        
        # Format token: tkn_key_timestamp_user_hash
        token = f'tkn_{self.api_key}_{epoch}_{self.user_role}_{hash_value}'
        
        return token
    
    def _parse_mindtouch_response(self, xml_response: str) -> str:
        """
        Parse MindTouch XML response to extract completion text
        
        Args:
            xml_response: Raw XML response from MindTouch API
            
        Returns:
            Parsed completion text or error message
        """
        try:
            # Parse XML response
            root = ET.fromstring(xml_response)
            
            # Look for completion element
            completion_elem = root.find('.//completion')
            if completion_elem is not None and completion_elem.text:
                completion_text = completion_elem.text.strip()
                print(f"✅ Parsed MindTouch completion ({len(completion_text)} chars)")
                return completion_text
            
            # Fallback: look for any text content in response
            response_elem = root.find('.//response')
            if response_elem is not None:
                # Get all text content from response element
                all_text = ''.join(response_elem.itertext()).strip()
                if all_text:
                    print(f"✅ Extracted text from response element ({len(all_text)} chars)")
                    return all_text
            
            # If no structured content found, return raw text
            print("⚠️  No completion/response elements found, using raw XML")
            return xml_response
            
        except ET.ParseError as e:
            print(f"⚠️  XML parsing failed: {e}, treating as plain text")
            return xml_response
        except Exception as e:
            print(f"⚠️  Response parsing error: {e}")
            return xml_response
    
    async def get_llm_response(self, query: str) -> str:
        """
        Get LLM response from MindTouch with role-based content filtering
        
        Args:
            query: User query string
            
        Returns:
            LLM response text or error message
        """
        try:
            customer_context = f" | Customer: {self.customer_org_info.get('organization', 'Unknown')}" if self.customer_email else ""
            print(f"🧠 MindTouch LLM Query: '{query}' (Role: {self.user_role}{customer_context})")
            
            # Generate authentication token
            token = self._generate_auth_token()
            
            # Encode query for URL
            encoded_query = urllib.parse.quote(query)
            
            # Construct the URL with the encoded query
            url = f"https://helpcenter.modeln.com/@api/deki/llm/completion?q={encoded_query}"
            
            print(f"📡 MindTouch URL: {url}")
            
            # Prepare headers
            headers = {
                'X-Deki-Token': token,
                'User-Agent': 'ModelN-QueryBot/1.0'
            }
            
            # Make the API request
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            
            print(f"📊 MindTouch Response: {response.status_code}")
            
            # Handle the response
            if response.status_code == 200:
                print("✅ MindTouch LLM response received")
                # Parse the XML response to extract completion text
                raw_response = response.text
                parsed_response = self._parse_mindtouch_response(raw_response)
                return parsed_response
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                print(f"❌ MindTouch API Error: {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"❌ MindTouch LLM error: {str(e)}"
            print(error_msg)
            return error_msg
    
    def search_pages(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search MindTouch using LLM completion API (backwards compatibility)
        
        Args:
            query: Search query string
            limit: Not used in LLM API but kept for compatibility
            
        Returns:
            List containing single result with LLM response
        """
        try:
            customer_context = f" | {self.customer_org_info.get('organization', 'Unknown')}" if self.customer_email else ""
            print(f"🔍 MindTouch LLM search: '{query}' (Role: {self.user_role}{customer_context})")
            
            # Use async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response_text = loop.run_until_complete(self.get_llm_response(query))
            finally:
                loop.close()
            
            # Check if LLM response indicates no relevant information found
            no_answer_indicators = [
                "no relevant",
                "not appear to be",
                "could not find",
                "no information",
                "cannot find",
                "unable to find",
                "does not have",
                "no answer",
                "no solution",
                "no specific",
                "not enough information",
                "insufficient information"
            ]
            
            response_lower = response_text.lower()
            has_no_answer = any(indicator in response_lower for indicator in no_answer_indicators)
            
            # Format response as a document for compatibility with existing system
            if not response_text.startswith("Error:") and not response_text.startswith("❌") and not has_no_answer:
                return [{
                    'id': 'llm_response',
                    'title': f'MindTouch Response for: {query[:50]}... | {self.customer_org_info.get("organization", "Unknown")}',
                    'path': '/llm/completion',
                    'summary': response_text,  # Keep full content - don't truncate
                    'content': response_text,  # Full content
                    'score': 1.0,  # High confidence for LLM response
                    'source': f'MindTouch LLM ({self.user_role})',
                    'user_role': self.user_role,
                    'customer_organization': self.customer_org_info.get('organization', 'Unknown'),
                    'customer_email': self.customer_email
                }]
            else:
                if has_no_answer:
                    print(f"🎫 MindTouch LLM indicates no relevant answer - will route to ticket creation")
                else:
                    print(f"❌ MindTouch LLM returned error: {response_text}")
                return []
                
        except Exception as e:
            print(f"❌ Error in MindTouch LLM search: {e}")
            return []
    
    def get_role_from_project_type(self, project_type: str) -> str:
        """
        Map project type to MindTouch user role
        
        Args:
            project_type: Project type (HIGH_TECH, LIFE_SCIENCES, etc.)
            
        Returns:
            MindTouch user role string
        """
        role_mapping = {
            'HIGH_TECH': '=GoS-HT',
            'LIFE_SCIENCES': '=GoS-LS', 
            'PBN': '=GoS-PBN',
            'PBF': '=GoS-PBF',
            'CDM': '=GoS-CDM',
            'GLOBAL': '=GoS-GLOBAL',
        }
        
        return role_mapping.get(project_type.upper(), '=customer')
    
    def test_connection(self) -> bool:
        """
        Test the connection to MindTouch LLM API
        
        Returns:
            True if connection is successful
        """
        try:
            print("🧪 Testing MindTouch LLM connection...")
            
            # Use async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                test_response = loop.run_until_complete(
                    self.get_llm_response("test connection")
                )
            finally:
                loop.close()
            
            success = not test_response.startswith("Error:") and not test_response.startswith("❌")
            
            if success:
                print("✅ MindTouch LLM connection successful")
            else:
                print(f"❌ MindTouch LLM connection failed: {test_response}")
                
            return success
            
        except Exception as e:
            print(f"❌ MindTouch LLM connection test failed: {e}")
            return False
