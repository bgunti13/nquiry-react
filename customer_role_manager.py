"""
Dynamic Customer Role Mapping Manager

Reads customer-to-role mappings from Excel file instead of hardcoded mappings.
Supports automatic refresh and easy management by non-technical users.
"""

import pandas as pd
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

class CustomerRoleMappingManager:
    def get_all_jira_organisations(self) -> List[str]:
        """
        Extract all organization names and aliases from the 'JIRA Organisation' column in LS and HT sheets
        Returns:
            List of organization names/aliases
        """
        org_names = set()
        if not os.path.exists(self.excel_file_path):
            return []
        try:
            xl_file = pd.ExcelFile(self.excel_file_path)
            for sheet_name in xl_file.sheet_names:
                if sheet_name.strip().upper() not in ['LS', 'HT']:
                    continue
                df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
                # Try different possible column names (including trailing space)
                possible_columns = [
                    'JIRA Organisation', 'JIRA Organization', 
                    'JIRA Organisation ', 'JIRA Organization '
                ]
                for col in possible_columns:
                    if col in df.columns:
                        for val in df[col].dropna().unique():
                            val = str(val).strip()
                            if val and val.lower() != 'nan' and val != '':
                                org_names.add(val)
                        break  # Found the column, no need to check other variants
            return list(org_names)
        except Exception as e:
            print(f"Error extracting JIRA Organisations: {e}")
            return []
    """
    Manages customer organization to MindTouch role mappings from Excel file
    """
    
    def __init__(self, excel_file_path: str = 'LS-HT Customer Info.xlsx'):
        self.excel_file_path = excel_file_path
        self.mappings = {}
        self.support_domains = set()  # Track Zendesk support email domains
        self.last_loaded = None
        self.file_last_modified = None
        
        # Role mapping from Excel platform codes to MindTouch roles
        self.platform_role_mapping = {
            'LS-N': 'GoS-PBN',      # Life Sciences - PBN
            'LS-Flex': 'GoS-PBF',   # Life Sciences - PBF  
            'HT': 'GoS-HT',         # High Tech
            # Add more mappings as needed
        }
        
        self.load_mappings()
    
    def load_mappings(self) -> bool:
        """
        Load customer mappings from Excel file (all sheets)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.excel_file_path):
                print(f"⚠️  Excel file not found: {self.excel_file_path}")
                return False
            
            # Check if file has been modified
            current_mtime = os.path.getmtime(self.excel_file_path)
            if self.file_last_modified == current_mtime and self.mappings:
                # File hasn't changed, skip loading
                return True
            
            print(f"📊 Loading customer mappings from {self.excel_file_path}")
            
            # Read all sheets from Excel file
            xl_file = pd.ExcelFile(self.excel_file_path)
            sheet_names = xl_file.sheet_names
            print(f"📄 Found {len(sheet_names)} sheets: {sheet_names}")
            
            # Clear existing mappings
            self.mappings = {}
            total_customers = 0
            
            # Process each sheet
            for sheet_name in sheet_names:
                print(f"\n📋 Processing sheet: '{sheet_name}'")
                
                # Skip non-customer data sheets
                sheet_name_clean = sheet_name.strip().lower()
                if sheet_name_clean in ['mapping', 'config', 'settings', 'field mapping', 'field mappings', 'jira fields', 'jira fields ']:
                    print(f"   ⏭️  Skipping non-customer sheet: '{sheet_name}'")
                    continue
                
                df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
                
                if df.empty:
                    print(f"   ⚠️  Sheet '{sheet_name}' is empty, skipping")
                    continue
                
                sheet_customers = 0
                
                # Process based on sheet name/type
                if sheet_name.upper() == 'LS':
                    # Life Sciences sheet - has Platform column
                    sheet_customers = self._process_ls_sheet(df, sheet_name)
                elif sheet_name.upper() == 'HT':
                    # High Tech sheet - assume all are HT
                    sheet_customers = self._process_ht_sheet(df, sheet_name)
                else:
                    # Unknown sheet type - try to auto-detect
                    if 'Platform' in df.columns:
                        sheet_customers = self._process_ls_sheet(df, sheet_name)
                    else:
                        # Assume HT if no Platform column
                        sheet_customers = self._process_ht_sheet(df, sheet_name)
                
                total_customers += sheet_customers
                print(f"   ✅ Processed {sheet_customers} customers from '{sheet_name}' sheet")
            
            self.last_loaded = datetime.now()
            self.file_last_modified = current_mtime
            
            print(f"\n🎯 Successfully loaded {total_customers} customer mappings ({len(self.mappings)} unique domains)")
            return True
            
        except Exception as e:
            print(f"❌ Error loading customer mappings: {e}")
            return False
    
    def _process_ls_sheet(self, df: pd.DataFrame, sheet_name: str) -> int:
        """Process Life Sciences sheet with Platform column"""
        customers_processed = 0
        
        # Check if required columns exist
        if 'Customer' not in df.columns:
            print(f"   ⚠️  Sheet '{sheet_name}' missing 'Customer' column, skipping")
            return 0
        if 'Platform' not in df.columns:
            print(f"   ⚠️  Sheet '{sheet_name}' missing 'Platform' column, skipping")
            return 0
        
        for _, row in df.iterrows():
            try:
                customer_name = str(row['Customer']).strip()
                platform = str(row['Platform']).strip()
                
                # Skip invalid entries
                if pd.isna(customer_name) or customer_name.lower() in ['nan', '']:
                    continue
                
                # Get role from platform
                role = self.platform_role_mapping.get(platform, 'customer')
                
                # Generate domain from customer name
                domain = self._generate_domain_from_name(customer_name)
                
                # Get Prod. Version if available
                prod_version = str(row.get('Prod. Version', '')).strip()
                if prod_version and prod_version.lower() == 'nan':
                    prod_version = ''

                # Extract Support Email Address if available
                support_email = str(row.get('Support Email Address', '')).strip()
                if support_email and support_email.lower() != 'nan' and '@' in support_email:
                    support_domain = support_email.split('@')[1].lower()
                    self.support_domains.add(support_domain)
                    print(f"      📧 Found support domain: {support_domain}")
                
                # Store mapping (avoid duplicates by using domain as key)
                if domain not in self.mappings:
                    self.mappings[domain] = {
                        'organization': customer_name,
                        'platform': platform,
                        'role': f"={role}",
                        'primary_role': f"={role}",
                        'roles': [f"={role}"],
                        'sheet': sheet_name,
                        'prod_version': prod_version or 'Unknown',
                        'support_email': support_email if support_email and support_email.lower() != 'nan' else None
                    }
                    customers_processed += 1
                    version_info = f" (Version: {prod_version})" if prod_version else ""
                    print(f"      ✅ {customer_name} ({domain}) → {role}{version_info}")
                else:
                    print(f"      ⚠️  Duplicate domain {domain} for {customer_name}, keeping existing")
                    
            except Exception as e:
                print(f"      ❌ Error processing row in sheet '{sheet_name}': {e}")
                continue
        
        return customers_processed
    
    def _process_ht_sheet(self, df: pd.DataFrame, sheet_name: str) -> int:
        """Process High Tech sheet (assume all are HT)"""
        customers_processed = 0
        
        # Check if required columns exist
        if 'Customer' not in df.columns:
            print(f"   ⚠️  Sheet '{sheet_name}' missing 'Customer' column, skipping")
            return 0
        
        for _, row in df.iterrows():
            try:
                customer_name = str(row['Customer']).strip()
                
                # Skip invalid entries
                if pd.isna(customer_name) or customer_name.lower() in ['nan', '']:
                    continue
                
                # All HT customers get GoS-HT role
                role = 'GoS-HT'
                platform = 'HT'
                
                # Generate domain from customer name
                domain = self._generate_domain_from_name(customer_name)
                
                # Get Prod. Version if available
                prod_version = str(row.get('Prod. Version', '')).strip()
                if prod_version and prod_version.lower() == 'nan':
                    prod_version = ''

                # Extract Support Email Address if available
                support_email = str(row.get('Support Email Address', '')).strip()
                if support_email and support_email.lower() != 'nan' and '@' in support_email:
                    support_domain = support_email.split('@')[1].lower()
                    self.support_domains.add(support_domain)
                    print(f"      📧 Found support domain: {support_domain}")
                
                # Store mapping (avoid duplicates)
                if domain not in self.mappings:
                    self.mappings[domain] = {
                        'organization': customer_name,
                        'platform': platform,
                        'role': f"={role}",
                        'primary_role': f"={role}",
                        'roles': [f"={role}"],
                        'sheet': sheet_name,
                        'prod_version': prod_version or 'Unknown',
                        'support_email': support_email if support_email and support_email.lower() != 'nan' else None
                    }
                    customers_processed += 1
                    version_info = f" (Version: {prod_version})" if prod_version else ""
                    print(f"      ✅ {customer_name} ({domain}) → {role}{version_info}")
                else:
                    print(f"      ⚠️  Duplicate domain {domain} for {customer_name}, keeping existing")
                    
            except Exception as e:
                print(f"      ❌ Error processing row in sheet '{sheet_name}': {e}")
                continue
        
        return customers_processed
    
    def _generate_domain_from_name(self, customer_name: str) -> str:
        """
        Generate email domain from customer name
        
        Args:
            customer_name: Company name
            
        Returns:
            Generated domain (e.g., "Abbott ADC" → "abbott.com")
        """
        # Clean the name
        clean_name = customer_name.lower()
        
        # Remove common suffixes and words
        remove_words = [
            'inc.', 'inc', 'corp.', 'corp', 'ltd.', 'ltd', 'llc', 'l.l.c.', 
            'pharmaceuticals', 'pharma', 'company', 'co.', 'co',
            '(not yet live)', 'limited', 'plc', 'group'
        ]
        
        for word in remove_words:
            clean_name = clean_name.replace(word, '')
        
        # Take first word as domain base
        domain_base = clean_name.split()[0].strip()
        
        # Remove special characters
        domain_base = ''.join(c for c in domain_base if c.isalnum())
        
        return f"{domain_base}.com"
    
    def get_customer_mapping(self, email_domain: str) -> Dict:
        """
        Get customer mapping for email domain
        
        Args:
            email_domain: Email domain (e.g., "abbott.com")
            
        Returns:
            Customer mapping dictionary or default customer mapping
        """
        # Auto-refresh if file has changed
        self.refresh_if_needed()
        
        # Direct domain match
        if email_domain in self.mappings:
            return self.mappings[email_domain]
        
        # Fallback: try to find partial matches
        for domain, mapping in self.mappings.items():
            # Check if domain contains email domain or vice versa
            domain_base = domain.replace('.com', '')
            email_base = email_domain.replace('.com', '')
            
            if domain_base in email_base or email_base in domain_base:
                print(f"🔍 Found partial match: {email_domain} → {mapping['organization']}")
                return mapping
        
        # Default fallback
        return {
            'organization': email_domain.replace('.com', '').upper(),
            'platform': 'Unknown',
            'role': '=customer',
            'primary_role': '=customer',
            'roles': ['=customer']
        }
    
    def refresh_if_needed(self) -> bool:
        """
        Refresh mappings if Excel file has been modified
        
        Returns:
            True if refresh was performed
        """
        if not os.path.exists(self.excel_file_path):
            return False
        
        current_mtime = os.path.getmtime(self.excel_file_path)
        if self.file_last_modified != current_mtime:
            print("🔄 Excel file updated, refreshing mappings...")
            return self.load_mappings()
        
        return False
    
    def get_all_mappings(self) -> Dict:
        """
        Get all current mappings
        
        Returns:
            Dictionary of all customer mappings
        """
        self.refresh_if_needed()
        return self.mappings.copy()
    
    def is_support_domain(self, email: str) -> bool:
        """
        Check if the given email belongs to a support domain (Zendesk workflow)
        
        Args:
            email: Email address to check
            
        Returns:
            True if email domain is a support domain, False otherwise
        """
        if not email or '@' not in email:
            return False
            
        domain = email.split('@')[1].lower()
        is_support = domain in self.support_domains
        
        if is_support:
            print(f"🎫 Support domain detected: {email} → Zendesk workflow")
        
        return is_support
    
    def get_support_domains(self) -> List[str]:
        """
        Get list of all support domains
        
        Returns:
            List of support email domains
        """
        return list(self.support_domains)
    
    def add_manual_mapping(self, domain: str, organization: str, role: str):
        """
        Manually add a mapping (useful for testing)
        
        Args:
            domain: Email domain
            organization: Organization name
            role: MindTouch role (without = prefix)
        """
        self.mappings[domain] = {
            'organization': organization,
            'platform': 'Manual',
            'role': f"={role}",
            'primary_role': f"={role}",
            'roles': [f"={role}"]
        }
        print(f"➕ Added manual mapping: {domain} → {organization} ({role})")
    
    def get_mapping_stats(self) -> Dict:
        """
        Get statistics about current mappings
        
        Returns:
            Dictionary with mapping statistics
        """
        self.refresh_if_needed()
        
        role_counts = {}
        for mapping in self.mappings.values():
            role = mapping['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            'total_customers': len(self.mappings),
            'role_distribution': role_counts,
            'last_loaded': self.last_loaded.strftime('%Y-%m-%d %H:%M:%S') if self.last_loaded else 'Never',
            'excel_file': self.excel_file_path,
            'file_exists': os.path.exists(self.excel_file_path)
        }


# Global instance for easy access
customer_role_manager = CustomerRoleMappingManager()


def get_customer_organization_info(email: str) -> Dict:
    """
    Get customer organization info from email (backwards compatibility)
    
    Args:
        email: Customer email address
        
    Returns:
        Organization info dictionary
    """
    if not email or '@' not in email:
        return {
            'organization': 'Unknown',
            'primary_role': '=customer',
            'roles': ['=customer']
        }
    
    domain = email.split('@')[1].lower()
    return customer_role_manager.get_customer_mapping(domain)


if __name__ == "__main__":
    # Test the mapping manager
    print("🧪 Testing Customer Role Mapping Manager")
    print("=" * 50)
    
    manager = CustomerRoleMappingManager()
    
    # Show stats
    stats = manager.get_mapping_stats()
    print(f"📊 Mapping Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test some mappings
    test_domains = ['abbott.com', 'amgen.com', 'pfizer.com', 'unknown.com']
    
    print(f"\n🔍 Testing domain mappings:")
    for domain in test_domains:
        mapping = manager.get_customer_mapping(domain)
        print(f"   {domain} → {mapping['organization']} ({mapping['role']})")
