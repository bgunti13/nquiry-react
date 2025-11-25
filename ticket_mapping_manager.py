"""
Dynamic Ticket Mapping Manager
Loads ticket mapping configuration from Excel sheet instead of hardcoded JSON.
Falls back to JSON if Excel is not available.
"""

import pandas as pd
import json
import os
from typing import Dict, Any, List

class TicketMappingManager:
    def __init__(self, excel_file_path: str = None, json_file_path: str = None):
        """
        Initialize the ticket mapping manager
        
        Args:
            excel_file_path: Path to the Excel file containing TicketMapping sheet
            json_file_path: Path to the fallback JSON configuration file
        """
        self.excel_file_path = excel_file_path or 'LS-HT Customer Info.xlsx'
        self.json_file_path = json_file_path or 'ticket_mapping_config.json'
        self.ticket_mapping = {}
        self.last_loaded_source = None
        
        # Load the mapping
        self._load_mapping()
    
    def _load_mapping(self):
        """Load ticket mapping from Excel first, fallback to JSON if needed"""
        try:
            # Try to load from Excel first
            self._load_from_excel()
            self.last_loaded_source = "Excel"
            print(f"✅ Loaded ticket mapping from Excel: {len(self.ticket_mapping.get('ticket_categories', {}))} categories")
        except Exception as excel_error:
            print(f"⚠️ Could not load from Excel ({excel_error}), falling back to JSON...")
            try:
                # Fallback to JSON
                self._load_from_json()
                self.last_loaded_source = "JSON"
                print(f"✅ Loaded ticket mapping from JSON: {len(self.ticket_mapping.get('ticket_categories', {}))} categories")
            except Exception as json_error:
                print(f"❌ Could not load from JSON either: {json_error}")
                self.ticket_mapping = {"ticket_categories": {}, "default_category": "MNHT"}
                self.last_loaded_source = "None"
    
    def _load_from_excel(self):
        """Load ticket mapping configuration from Excel TicketMapping sheet"""
        if not os.path.exists(self.excel_file_path):
            raise FileNotFoundError(f"Excel file not found: {self.excel_file_path}")
        
        # Use context manager to ensure file is properly closed
        try:
            # Read the TicketMapping sheet with explicit engine and close after reading
            with pd.ExcelFile(self.excel_file_path, engine='openpyxl') as excel_file:
                df = pd.read_excel(excel_file, sheet_name='TicketMapping')
        except Exception as e:
            raise Exception(f"Failed to read TicketMapping sheet: {e}")
        
        # Convert to the expected JSON-like structure
        ticket_categories = {}
        default_category = "MNHT"  # Default fallback
        
        for _, row in df.iterrows():
            category = str(row.get('Category', '')).strip()
            active = str(row.get('Active', 'Yes')).strip().lower()
            
            # Skip inactive categories
            if active == 'no' or active == 'false' or not category:
                continue
            
            # Parse keywords
            keywords_str = str(row.get('Keywords', ''))
            keywords = [k.strip() for k in keywords_str.split(';') if k.strip()] if keywords_str != 'nan' else []
            
            # Parse required fields
            required_fields_str = str(row.get('Required_Fields', ''))
            required_fields = {}
            if required_fields_str and required_fields_str != 'nan':
                for field in required_fields_str.split(';'):
                    field = field.strip()
                    if field:
                        required_fields[field] = f"Description of the {field}"
            
            # Build populated fields
            populated_fields = {}
            field_mappings = {
                'Project': 'project',
                'Work_Type': 'work_type', 
                'Priority': 'priority',
                'Request_Type': 'request_type',
                'Urgency': 'urgency',
                'Impact': 'impact',
                'Cloud_Operations_Request_Type': 'cloud_operations_request_type',
                'Cloud_Environmental_List': 'cloud_environmental_list',
                'Support_Org': 'support_org',
                'JSD_Suppress_Group_Email_Notification': 'jsd_suppress_group_email_notification'
            }
            
            for excel_col, json_field in field_mappings.items():
                value = str(row.get(excel_col, '')).strip()
                if value and value != 'nan':
                    populated_fields[json_field] = value
            
            # Add dynamic fields
            populated_fields['summary'] = 'Generated based on description'
            populated_fields['customer'] = 'Based on customer organization'
            if 'cloud_operations_request_date' not in populated_fields and category == 'COPS':
                populated_fields['cloud_operations_request_date'] = 'current_date'
            if 'support_projects' not in populated_fields and category == 'COPS':
                populated_fields['support_projects'] = 'Based on customer sheet mapping'
            
            # Parse work type options if available
            work_type_options = {}
            work_type_options_str = str(row.get('Work_Type_Options', ''))
            if work_type_options_str and work_type_options_str != 'nan':
                try:
                    work_type_options = json.loads(work_type_options_str)
                except:
                    # If JSON parsing fails, ignore work type options
                    pass
            
            # Build category configuration
            category_config = {
                'keywords': keywords,
                'required_fields': required_fields,
                'populated_fields': populated_fields
            }
            
            if work_type_options:
                category_config['work_type_options'] = work_type_options
            
            ticket_categories[category] = category_config
        
        # Build the final mapping structure
        self.ticket_mapping = {
            'ticket_categories': ticket_categories,
            'default_category': default_category
        }
        
        if not ticket_categories:
            raise ValueError("No active ticket categories found in Excel sheet")
    
    def _load_from_json(self):
        """Load ticket mapping configuration from JSON file (fallback)"""
        if not os.path.exists(self.json_file_path):
            raise FileNotFoundError(f"JSON file not found: {self.json_file_path}")
        
        with open(self.json_file_path, 'r') as f:
            self.ticket_mapping = json.load(f)
    
    def get_mapping(self) -> Dict[str, Any]:
        """Get the complete ticket mapping configuration"""
        return self.ticket_mapping
    
    def get_categories(self) -> Dict[str, Any]:
        """Get just the ticket categories"""
        return self.ticket_mapping.get('ticket_categories', {})
    
    def get_category(self, category_name: str) -> Dict[str, Any]:
        """Get configuration for a specific category"""
        return self.get_categories().get(category_name, {})
    
    def get_default_category(self) -> str:
        """Get the default category name"""
        return self.ticket_mapping.get('default_category', 'MNHT')
    
    def reload(self):
        """Reload the mapping configuration"""
        self._load_mapping()
    
    def get_source_info(self) -> str:
        """Get information about where the mapping was loaded from"""
        return f"Loaded from: {self.last_loaded_source}"
    
    def get_active_categories(self) -> List[str]:
        """Get list of active category names"""
        return list(self.get_categories().keys())

# Global instance for easy import
ticket_mapping_manager = TicketMappingManager()

def get_ticket_mapping() -> Dict[str, Any]:
    """Convenience function to get ticket mapping"""
    return ticket_mapping_manager.get_mapping()

def reload_ticket_mapping():
    """Convenience function to reload ticket mapping"""
    ticket_mapping_manager.reload()

if __name__ == "__main__":
    # Test the mapping manager
    print("🧪 Testing Ticket Mapping Manager...")
    
    manager = TicketMappingManager()
    print(f"\n{manager.get_source_info()}")
    
    categories = manager.get_active_categories()
    print(f"Active categories: {categories}")
    
    for category in categories[:2]:  # Show first 2 categories as example
        config = manager.get_category(category)
        print(f"\n{category} configuration:")
        print(f"  Keywords: {config.get('keywords', [])[:3]}...")  # First 3 keywords
        print(f"  Project: {config.get('populated_fields', {}).get('project', 'N/A')}")
        print(f"  Work Type: {config.get('populated_fields', {}).get('work_type', 'N/A')}")