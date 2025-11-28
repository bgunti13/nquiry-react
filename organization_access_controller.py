"""
Organization Access Control Manager

Detects when users query information about organizations outside their own
and blocks access with appropriate messaging.
"""

import re
import os
from typing import List, Dict, Optional
from customer_role_manager import CustomerRoleMappingManager


class OrganizationAccessController:
    """
    Manages cross-organization access control for queries
    """
    
    def __init__(self):
        self.customer_manager = CustomerRoleMappingManager()
        self.all_jira_organizations = []
        self.org_name_to_aliases = {}  # Maps full org name to list of aliases/short names
        self.refresh_organizations()
    
    def refresh_organizations(self):
        """Refresh the list of all organization names/aliases from Excel"""
        try:
            self.all_jira_organizations = self.customer_manager.get_all_jira_organisations()
            self.org_name_to_aliases = self._build_org_aliases_mapping()
            print(f"📋 Loaded {len(self.all_jira_organizations)} organization names/aliases for access control")
            print(f"🔗 Built aliases for {len(self.org_name_to_aliases)} organizations")
        except Exception as e:
            print(f"⚠️ Error loading organization names: {e}")
            self.all_jira_organizations = []
            self.org_name_to_aliases = {}
    
    def _build_org_aliases_mapping(self) -> Dict[str, List[str]]:
        """
        Build mapping of organization names to their aliases/short names from Excel Customer column
        Returns:
            Dictionary mapping full org name to list of aliases
        """
        org_aliases = {}
        
        if not os.path.exists(self.customer_manager.excel_file_path):
            return {}
        
        try:
            import pandas as pd
            xl_file = pd.ExcelFile(self.customer_manager.excel_file_path)
            
            for sheet_name in xl_file.sheet_names:
                if sheet_name.strip().upper() not in ['LS', 'HT']:
                    continue
                    
                df = pd.read_excel(self.customer_manager.excel_file_path, sheet_name=sheet_name)
                
                # Check if required columns exist
                if 'Customer' not in df.columns:
                    continue
                
                # Find the JIRA Organization column (with possible trailing space)
                jira_org_col = None
                for col in ['JIRA Organisation', 'JIRA Organization', 'JIRA Organisation ', 'JIRA Organization ']:
                    if col in df.columns:
                        jira_org_col = col
                        break
                
                if not jira_org_col:
                    continue
                
                # Build mapping
                for _, row in df.iterrows():
                    customer = str(row.get('Customer', '')).strip()
                    jira_org = str(row.get(jira_org_col, '')).strip()
                    
                    if customer and jira_org and customer.lower() != 'nan' and jira_org.lower() != 'nan':
                        if jira_org not in org_aliases:
                            org_aliases[jira_org] = []
                        
                        # Add customer name as alias if it's different from the org name
                        if customer.lower() != jira_org.lower():
                            org_aliases[jira_org].append(customer)
                        
                        # Extract potential short names from customer name
                        # Handle patterns like "AMD (Xilinx)", "WDC", etc.
                        customer_clean = customer.replace('(', '').replace(')', '').strip()
                        
                        # Split and add individual parts
                        parts = customer_clean.split()
                        
                        # Common words to exclude from aliases
                        excluded_words = {
                            'inc', 'corp', 'ltd', 'llc', 'company', 'co', 'group', 'international',
                            'pharmaceuticals', 'pharma', 'technologies', 'technology', 'systems',
                            'not', 'yet', 'live', 'and', 'the', 'of', 'for', 'in', 'on', 'at',
                            'with', 'by', 'from', 'to', 'a', 'an', 'is', 'are', 'was', 'were'
                        }
                        
                        for part in parts:
                            part_clean = part.strip('(),').lower()
                            # Only add if it's long enough and not a common word
                            if (len(part_clean) >= 2 and 
                                part_clean not in excluded_words and
                                part.strip('(),') not in org_aliases[jira_org]):
                                org_aliases[jira_org].append(part.strip('(),'))
        
        except Exception as e:
            print(f"⚠️ Error building org aliases mapping: {e}")
        
        return org_aliases
    
    def get_user_organization_info(self, customer_email: str) -> Optional[Dict]:
        """
        Get comprehensive organization info for the user including version
        
        Args:
            customer_email: User's email address
            
        Returns:
            Dictionary with organization details including version
        """
        if not customer_email or '@' not in customer_email:
            return None
        
        domain = customer_email.split('@')[-1].lower()
        customer_mapping = self.customer_manager.get_customer_mapping(domain)
        
        return {
            'organization': customer_mapping.get('organization', domain.replace('.com', '').upper()),
            'platform': customer_mapping.get('platform', 'Unknown'),
            'prod_version': customer_mapping.get('prod_version', 'Unknown'),
            'sheet': customer_mapping.get('sheet', 'Unknown'),
            'domain': domain
        }
    
    def detect_other_organizations_in_query(self, query: str, user_organization: str) -> List[str]:
        """
        Detect references to other organizations in the query
        
        Args:
            query: User's query text
            user_organization: User's organization name
            
        Returns:
            List of other organization names found in the query
        """
        if not self.all_jira_organizations:
            self.refresh_organizations()
        
        query_lower = query.lower()
        user_org_lower = user_organization.lower() if user_organization else ""
        other_orgs_found = []
        
        for org_name in self.all_jira_organizations:
            if not org_name:
                continue
                
            org_lower = org_name.lower()
            
            # Skip if this is the user's organization
            if org_lower == user_org_lower:
                continue
            
            # Get all possible search patterns for this organization
            search_patterns = []
            
            # 1. Full organization name
            search_patterns.append(org_lower)
            
            # 2. Add aliases from Excel Customer column
            if org_name in self.org_name_to_aliases:
                for alias in self.org_name_to_aliases[org_name]:
                    search_patterns.append(alias.lower())
            
            # Check each pattern against the query
            for pattern in search_patterns:
                if not pattern or len(pattern) < 2:
                    continue
                # Use word boundaries to ensure we match whole words
                word_pattern = r'\b' + re.escape(pattern) + r'\b'
                if re.search(word_pattern, query_lower):
                    other_orgs_found.append(org_name)
                    break  # Found a match for this org, no need to check other patterns
        
        return other_orgs_found
    
    def check_query_access(self, query: str, customer_email: str) -> Dict:
        """
        Check if a query attempts to access data from other organizations
        
        Args:
            query: User's query text
            customer_email: User's email address
            
        Returns:
            Dictionary with 'allowed' (bool), 'message' (str), 'blocked_orgs' (list), 'user_info' (dict)
        """
        user_info = self.get_user_organization_info(customer_email)
        
        if not user_info:
            # If we can't determine user org, allow the query (default behavior)
            return {
                'allowed': True,
                'message': '',
                'blocked_orgs': [],
                'user_info': None
            }
        
        user_org = user_info['organization']
        blocked_orgs = self.detect_other_organizations_in_query(query, user_org)
        
        if blocked_orgs:
            # Enhanced message with version information
            message = f"Sorry, couldn't access that data as it is out of your org. Your organization: {user_org} (Version: {user_info['prod_version']})"
            
            return {
                'allowed': False,
                'message': message,
                'blocked_orgs': blocked_orgs,
                'user_info': user_info
            }
        
        return {
            'allowed': True,
            'message': '',
            'blocked_orgs': [],
            'user_info': user_info
        }
    
    def get_organization_stats(self) -> Dict:
        """Get statistics about loaded organizations"""
        return {
            'total_organizations': len(self.all_jira_organizations),
            'organizations': self.all_jira_organizations[:10],  # First 10 for display
            'has_data': len(self.all_jira_organizations) > 0,
            'total_with_aliases': len(self.org_name_to_aliases),
            'sample_aliases': {k: v[:3] for k, v in list(self.org_name_to_aliases.items())[:3]}  # Sample aliases
        }


# Global instance for easy access
org_access_controller = OrganizationAccessController()


def check_organization_access(query: str, customer_email: str) -> Dict:
    """
    Convenience function to check organization access
    
    Args:
        query: User's query text
        customer_email: User's email address
        
    Returns:
        Access control result dictionary
    """
    return org_access_controller.check_query_access(query, customer_email)


if __name__ == "__main__":
    # Test the organization access controller
    print("🧪 Testing Organization Access Controller")
    print("=" * 50)
    
    controller = OrganizationAccessController()
    
    # Show stats
    stats = controller.get_organization_stats()
    print(f"📊 Organization Statistics:")
    for key, value in stats.items():
        if key == 'organizations':
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    # Test queries
    test_cases = [
        ("what is the status of amd project", "user@novartis.com"),
        ("tell me about wdc systems", "user@amd.com"),
        ("how do I configure my system", "user@abbott.com"),
        ("show me novartis documentation", "user@amd.com")
    ]
    
    print(f"\n🔍 Testing Access Control:")
    for query, email in test_cases:
        result = controller.check_query_access(query, email)
        status = "❌ BLOCKED" if not result['allowed'] else "✅ ALLOWED"
        user_info = result.get('user_info', {})
        user_version = f" (Version: {user_info.get('prod_version', 'Unknown')})" if user_info else ""
        print(f"   {status} | {email}{user_version} | '{query}'")
        if not result['allowed']:
            print(f"     → {result['message']}")
            if result['blocked_orgs']:
                print(f"     → Blocked orgs: {result['blocked_orgs']}")