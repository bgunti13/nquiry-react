"""
Ticket creator module for creating support tickets when no relevant information is found
"""

from typing import Dict, Optional
import json
import os
from datetime import datetime

class TicketCreator:
    """
    Creates support tickets when no relevant information is found in knowledge bases
    """
    
    def __init__(self):
        # Load ticket configuration
        config_path = os.path.join(os.path.dirname(__file__), 'ticket_mapping_config.json')
        with open(config_path, 'r') as f:
            self.ticket_config = json.load(f)
        
        # Load customer mappings
        self.customer_email_to_category = {
            'amd.com': 'MNHT',
            'novartis.com': 'MNLS',
            'wdc.com': 'MNHT',
            'abbott.com': 'MNHT',
            'abbvie.com': 'MNLS'
        }
    
    def create_ticket(self, query: str, customer_email: str = None) -> Dict:
        """
        Create a ticket based on query and customer information
        """
        print(f"\n🎫 TICKET CREATION INITIATED")
        print("=" * 50)
        
        # Extract customer domain if email provided
        customer = "UNKNOWN"
        if customer_email:
            domain = customer_email.split('@')[-1].lower()
            # Map specific domains to customer names
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',  
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie'
            }
            customer = domain_to_customer.get(domain, domain.split('.')[0].capitalize())
        
        # Determine ticket category
        category = self.determine_ticket_category(query, customer)
        print(f"🏷️  Category: {category}")
        print(f"👤 Customer: {customer}")
        
        # Collect user inputs for required fields
        ticket_data = self.collect_user_input_for_category(category, query, customer, customer_email)
        
        # Generate ticket ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticket_id = f"TICKET_{category}_{customer}_{timestamp}"
        ticket_data['ticket_id'] = ticket_id
        ticket_data['category'] = category
        ticket_data['customer'] = customer
        ticket_data['created_date'] = datetime.now().isoformat()
        ticket_data['customer_email'] = customer_email
        ticket_data['original_query'] = query
        
        # Add auto-populated fields
        auto_fields = self.get_populated_fields_for_category(category)
        for field, value in auto_fields.items():
            if field not in ticket_data:
                ticket_data[field] = value
        
        # Save ticket to file
        output_dir = "ticket_simulation_output"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"ticket_demo_{category}_{customer}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"TICKET SIMULATION OUTPUT\n")
            f.write(f"========================\n\n")
            f.write(f"Ticket ID: {ticket_data['ticket_id']}\n")
            f.write(f"Category: {ticket_data['category']}\n")
            f.write(f"Customer: {ticket_data['customer']}\n")
            f.write(f"Created: {ticket_data['created_date']}\n")
            f.write(f"Customer Email: {ticket_data['customer_email']}\n")
            f.write(f"Original Query: {ticket_data['original_query']}\n\n")
            
            f.write("TICKET DETAILS:\n")
            f.write("===============\n")
            for key, value in ticket_data.items():
                if key not in ['ticket_id', 'category', 'customer', 'created_date', 'customer_email', 'original_query']:
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")
        
        # Display comprehensive ticket details
        print(f"\n✅ Ticket simulation completed!")
        print(f"🎫 Ticket ID: {ticket_data['ticket_id']}")
        print(f"📂 Category: {ticket_data['category']}")
        print(f"👤 Customer: {ticket_data['customer']}")
        print(f"📄 Document saved: {filepath}")
        
        # Display all ticket fields
        print(f"\n📋 COMPLETE TICKET DETAILS:")
        print("=" * 50)
        
        # Exclude metadata fields from display
        excluded_fields = {
            'category', 'ticket_id', 'created_date', 'customer_email', 
            'customer', 'original_query'
        }
        
        # Show user-provided fields
        print("🔹 PROVIDED FIELDS:")
        user_fields_shown = False
        required_fields = self.get_required_fields_for_category(ticket_data['category'])
        for field, value in ticket_data.items():
            if field not in excluded_fields and field in required_fields.keys():
                field_name = field.replace('_', ' ').title()
                print(f"   • {field_name}: {value}")
                user_fields_shown = True
        
        if not user_fields_shown:
            print("   • Description: " + ticket_data.get('description', 'N/A'))
        
        # Show auto-populated fields
        print("\n🤖 AUTO-POPULATED FIELDS:")
        auto_fields = self.get_populated_fields_for_category(ticket_data['category'])
        for field in auto_fields.keys():
            if field in ticket_data:
                field_name = field.replace('_', ' ').title()
                print(f"   • {field_name}: {ticket_data[field]}")
        
        print("=" * 50)
        
        return ticket_data
    
    def create_ticket_streamlit(self, query: str, customer_email: str = None, form_data: Dict = None) -> Dict:
        """
        Create a ticket using Streamlit form data (non-interactive)
        
        Args:
            query: Original user query
            customer_email: Customer email address
            form_data: Dictionary containing form data from Streamlit
            
        Returns:
            Dictionary containing ticket information
        """
        print(f"\n🎫 STREAMLIT TICKET CREATION")
        print("=" * 50)
        
        # Extract customer domain if email provided
        customer = "UNKNOWN"
        if customer_email:
            domain = customer_email.split('@')[-1].lower()
            # Map specific domains to customer names
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',  
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie'
            }
            customer = domain_to_customer.get(domain, domain.split('.')[0].capitalize())
        
        # Determine ticket category
        category = self.determine_ticket_category(query, customer)
        
        print(f"🏷️  Category: {category}")
        print(f"👤 Customer: {customer}")
        
        # Create base ticket data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticket_id = f"TICKET_{category}_{customer}_{timestamp}"
        
        ticket_data = {
            'ticket_id': ticket_id,
            'category': category,
            'customer': customer,
            'customer_email': customer_email,
            'created_date': datetime.now().isoformat(),
            'original_query': query
        }
        
        # Add form data if provided
        if form_data:
            ticket_data.update(form_data)
        
        # Auto-populate fields based on category
        populated_fields = self.get_populated_fields_for_category(category)
        for field, value in populated_fields.items():
            if field not in ticket_data:  # Don't override form data
                ticket_data[field] = value
        
        # Save ticket to file
        self.save_ticket_to_file(ticket_data)
        
        print(f"✅ Streamlit ticket created successfully: {ticket_id}")
        
        return ticket_data
    
    def determine_ticket_category(self, query: str, customer: str) -> str:
        """
        Determine the appropriate ticket category based on query content and customer
        Keyword matching takes precedence over customer mapping
        Prioritizes longer, more specific keywords over shorter ones
        """
        query_lower = query.lower()
        
        # Collect all matching keywords with their categories and lengths
        matches = []
        for category, config in self.ticket_config["ticket_categories"].items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    matches.append((len(keyword), keyword, category))
        
        # If matches found, return the category of the longest (most specific) keyword
        if matches:
            # Sort by keyword length (descending) to prioritize longer keywords
            matches.sort(key=lambda x: x[0], reverse=True)
            longest_keyword = matches[0][1]
            category = matches[0][2]
            print(f"🎯 Keyword match: '{longest_keyword}' found in query -> Category: {category}")
            return category
        
        # If no keyword match found, use customer-specific fallback mapping
        customer_to_category = {
            'AMD': 'MNHT',
            'NOVARTIS': 'MNLS', 
            'WDC': 'MNHT',
            'ABBOTT': 'MNHT',
            'ABBVIE': 'MNLS'
        }
        
        if customer in customer_to_category:
            print(f"🏢 Customer fallback: {customer} -> Category: {customer_to_category[customer]}")
            return customer_to_category[customer]
        
        # Default fallback
        default_category = self.ticket_config.get("default_category", "MNHT")
        print(f"⚠️ Using default category: {default_category}")
        return default_category
    
    def get_required_fields_for_category(self, category: str) -> Dict:
        """Get required fields for a specific category"""
        categories = self.ticket_config.get("ticket_categories", {})
        if category in categories:
            return categories[category].get("required_fields", {})
        return {}
    
    def get_populated_fields_for_category(self, category: str) -> Dict:
        """Get auto-populated fields for a specific category"""
        categories = self.ticket_config.get("ticket_categories", {})
        if category in categories:
            return categories[category].get("populated_fields", {})
        return {}
    
    def collect_user_input_for_category(self, category: str, query: str, customer: str, customer_email: str) -> Dict:
        """
        Collect user input for required fields based on category
        """
        ticket_data = {}
        required_fields = self.get_required_fields_for_category(category)
        
        print(f"\n📝 Collecting information for {category} ticket:")
        print("-" * 40)
        
        for field_name, field_description in required_fields.items():
            # Check if description already contains "(Optional)"
            if "(Optional)" in field_description:
                prompt = f"{field_description}: "
            else:
                prompt = f"{field_description}: "
            
            # For description field, suggest using the original query
            if field_name == 'description':
                suggested_value = query
                user_input = input(f"{prompt}(Press Enter to use: '{suggested_value}') ").strip()
                if not user_input:
                    user_input = suggested_value
            else:
                user_input = input(prompt).strip()
            
            if user_input:
                ticket_data[field_name] = user_input
            elif "(Optional)" not in field_description:
                # For required fields, keep asking until we get input
                while not user_input:
                    user_input = input(f"⚠️  {field_name} is required. {prompt}").strip()
                ticket_data[field_name] = user_input
        
        return ticket_data
    
    def create_ticket_streamlit(self, query: str, customer_email: str = None, ticket_data: dict = None) -> Dict:
        """
        Create a ticket for Streamlit interface with pre-filled data
        
        Args:
            query: Original user query
            customer_email: Customer email address
            ticket_data: Pre-filled ticket data from the form
            
        Returns:
            Dictionary containing ticket information
        """
        print(f"\n🎫 TICKET CREATION INITIATED (Streamlit)")
        print("=" * 50)
        
        # Extract customer domain if email provided
        customer = "UNKNOWN"
        if customer_email:
            domain = customer_email.split('@')[-1].lower()
            # Map specific domains to customer names
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',  
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie'
            }
            customer = domain_to_customer.get(domain, domain.split('.')[0].capitalize())
        
        # Determine ticket category based on customer email domain
        category = self.get_category_from_email(customer_email) if customer_email else 'MNHT'
        
        print(f"🏷️  Category: {category}")
        print(f"👤 Customer: {customer}")
        
        # Generate unique ticket ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticket_id = f"TICKET_{category}_{customer}_{timestamp}"
        
        # Prepare final ticket data
        final_ticket_data = {
            'ticket_id': ticket_id,
            'category': category,
            'customer': customer,
            'customer_email': customer_email,
            'original_query': query,
            'created_date': datetime.now().isoformat(),
            **ticket_data  # Merge in the form data
        }
        
        # Add auto-populated fields for the category
        auto_fields = self.get_populated_fields_for_category(category)
        final_ticket_data.update(auto_fields)
        
        # Save ticket to file
        os.makedirs('ticket_simulation_output', exist_ok=True)
        filepath = os.path.join('ticket_simulation_output', f"{ticket_id}.txt")
        
        with open(filepath, 'w') as f:
            f.write("SUPPORT TICKET SIMULATION\n")
            f.write("=" * 50 + "\n\n")
            
            for key, value in final_ticket_data.items():
                formatted_key = key.replace('_', ' ').title()
                f.write(f"{formatted_key}: {value}\n")
        
        print(f"📄 Document saved: {filepath}")
        print(f"✅ Ticket created successfully: {ticket_id}")
        
        return final_ticket_data

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
    
    def create_ticket_streamlit(self, query: str, customer_email: str = None, form_data: Dict = None) -> Dict:
        """
        Create a ticket for Streamlit interface with pre-filled form data
        
        Args:
            query: Original user query
            customer_email: Customer email for categorization
            form_data: Dictionary containing form data from Streamlit UI
            
        Returns:
            Dictionary containing ticket information
        """
        print(f"\n🎫 STREAMLIT TICKET CREATION INITIATED")
        print("=" * 50)
        
        # Extract customer domain if email provided
        customer = "UNKNOWN"
        if customer_email:
            domain = customer_email.split('@')[-1].lower()
            # Map specific domains to customer names
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',  
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie'
            }
            customer = domain_to_customer.get(domain, domain.split('.')[0].capitalize())
        
        # Determine category based on customer domain
        category = self.determine_ticket_category(query, customer)
        
        print(f"🏷️  Category: {category}")
        print(f"👤 Customer: {customer}")
        
        # Create base ticket data
        ticket_data = {
            'category': category,
            'customer': customer,
            'customer_email': customer_email or 'unknown@example.com',
            'original_query': query,
            'created_date': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'ticket_id': f"TICKET_{category}_{customer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Add form data if provided
        if form_data:
            # Map Streamlit form fields to ticket fields
            field_mapping = {
                'description': 'description',
                'priority': 'priority', 
                'area_affected': 'area_affected',
                'version_affected': 'version_affected',
                'environment': 'environment'
            }
            
            for streamlit_field, ticket_field in field_mapping.items():
                if streamlit_field in form_data:
                    ticket_data[ticket_field] = form_data[streamlit_field]
        
        # Populate category-specific fields
        auto_fields = self.get_populated_fields_for_category(category)
        for field, default_value in auto_fields.items():
            if field not in ticket_data:  # Only add if not already set
                ticket_data[field] = default_value
        
        # Generate summary if not provided
        if 'summary' not in ticket_data:
            summary = f"Support Request: {query[:100]}{'...' if len(query) > 100 else ''}"
            ticket_data['summary'] = summary
        
        # Save ticket simulation to file
        filename = f"ticket_demo_{category}_{customer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_dir = os.path.join(os.path.dirname(__file__), 'ticket_simulation_output')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("TICKET SIMULATION - STREAMLIT CREATED\n")
            f.write("="*60 + "\n")
            f.write(f"Ticket ID: {ticket_data['ticket_id']}\n")
            f.write(f"Category: {ticket_data['category']}\n")
            f.write(f"Customer: {ticket_data['customer']}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Original Query: {ticket_data['original_query']}\n")
            f.write("-"*60 + "\n")
            f.write("TICKET FIELDS:\n")
            f.write("-"*60 + "\n")
            
            # Write all ticket fields
            for field, value in ticket_data.items():
                if field not in ['ticket_id', 'category', 'customer', 'created_date', 'original_query']:
                    field_name = field.replace('_', ' ').title()
                    f.write(f"{field_name}: {value}\n")
            
            f.write("="*60 + "\n")
        
        print(f"✅ Ticket created successfully: {ticket_data['ticket_id']}")
        print(f"📂 Category: {ticket_data['category']}")
        print(f"👤 Customer: {ticket_data['customer']}")
        print(f"📄 Document saved: {filepath}")
        
        return ticket_data
        
    def save_ticket_to_file(self, ticket_data: Dict):
        """Save ticket data to file"""
        # Generate filename
        filename = f"ticket_demo_{ticket_data['category']}_{ticket_data['customer']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_dir = os.path.join(os.path.dirname(__file__), 'ticket_simulation_output')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        # Write ticket data to file
        with open(filepath, 'w') as f:
            f.write(f"TICKET SIMULATION OUTPUT\n")
            f.write(f"========================\n\n")
            f.write(f"Ticket ID: {ticket_data['ticket_id']}\n")
            f.write(f"Category: {ticket_data['category']}\n")
            f.write(f"Customer: {ticket_data['customer']}\n")
            f.write(f"Created: {ticket_data['created_date']}\n")
            f.write(f"Customer Email: {ticket_data.get('customer_email', 'N/A')}\n")
            f.write(f"Original Query: {ticket_data['original_query']}\n\n")
            
            f.write("TICKET DETAILS:\n")
            f.write("===============\n")
            for key, value in ticket_data.items():
                if key not in ['ticket_id', 'category', 'customer', 'created_date', 'customer_email', 'original_query']:
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")
        
        print(f"📄 Document saved: {filepath}")