"""
Demo script for ticket creation simulation
This demonstrates the automatic ticket creation functionality when customers say 'yes' to ticket creation.
"""

from response_formatter import ResponseFormatter
import json

def demo_ticket_creation():
    """Demonstrate the ticket creation simulation for different scenarios"""
    
    print("🎫 nQuiry Ticket Creation Simulation Demo")
    print("="*60)
    print()
    
    # Initialize the response formatter
    formatter = ResponseFormatter()
    
    # Demo scenarios based on different categories
    scenarios = [
        {
            "name": "COPS - Database Issue (AMD Customer)",
            "query": "Database refresh is failing in production environment",
            "user_email": "admin@amd.com",
            "additional_description": "Error occurs during nightly refresh process. Application becomes unresponsive."
        },
        {
            "name": "NOC - Access Request",
            "query": "Need access to monitoring dashboard for server outage investigation",
            "user_email": "support@company.com",
            "additional_description": "Urgent access needed to troubleshoot production outage"
        },
        {
            "name": "MNLS - Product Support (Novartis)",
            "query": "How to configure user permissions in Model N Life Sciences version 2.3",
            "user_email": "helpdesk@novartis.com",
            "additional_description": "Need step-by-step guide for new user onboarding process"
        },
        {
            "name": "CSP - Access Management",
            "query": "Revoke access for terminated employee John Smith",
            "user_email": "hr@company.com",
            "additional_description": "Employee terminated on 2024-01-15, immediate access revocation required"
        },
        {
            "name": "MNHT - Technical Issue (AMD)",
            "query": "Application crashes when processing large data files in Model N Hi-Tech",
            "user_email": "support@amd.com",
            "additional_description": "Occurs with files larger than 100MB, affects multiple users"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"📋 Demo Scenario {i}: {scenario['name']}")
        print("-" * 50)
        print(f"User Query: {scenario['query']}")
        print(f"User Email: {scenario['user_email']}")
        print(f"Additional Details: {scenario['additional_description']}")
        print()
        
        # Simulate the "Would you like to create a ticket?" -> "Yes" flow
        print("❓ If you are not satisfied with this response, would you like me to create a support ticket for further assistance?")
        print("💬 Customer Response: Yes")
        print()
        
        # Create the simulated ticket
        try:
            ticket_response = formatter.create_simulated_ticket(
                query=scenario['query'],
                user_email=scenario['user_email'],
                additional_description=scenario['additional_description']
            )
            
            print(ticket_response)
            
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
        
        print("\n" + "="*60 + "\n")
        
        # Pause between scenarios for readability
        if i < len(scenarios):
            input("Press Enter to continue to next scenario...")
            print()

def demo_category_mapping():
    """Demonstrate how queries are mapped to different ticket categories"""
    
    print("🎯 Category Mapping Demo")
    print("="*40)
    
    # Load the ticket mapping configuration
    try:
        with open('ticket_mapping_config.json', 'r') as f:
            config = json.load(f)
        
        print("📋 Available Ticket Categories:")
        for category, details in config['ticket_categories'].items():
            print(f"\n🏷️  {category}:")
            print(f"   Keywords: {', '.join(details['keywords'][:5])}...")  # Show first 5 keywords
            print(f"   Required Fields: {', '.join(details['required_fields'].keys())}")
            
        print("\n🏢 Customer Domain Mappings:")
        for domain, category in config['customer_mappings'].items():
            print(f"   {domain} → {category}")
            
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")

def interactive_demo():
    """Interactive demo where user can input their own query"""
    
    print("🎮 Interactive Ticket Creation Demo")
    print("="*40)
    print("Enter your own query to see how it would be categorized and what ticket would be created.")
    print()
    
    formatter = ResponseFormatter()
    
    while True:
        query = input("💬 Enter your query (or 'quit' to exit): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not query:
            print("Please enter a valid query.")
            continue
            
        user_email = input("📧 Enter user email (optional): ").strip()
        additional_details = input("📝 Additional details (optional): ").strip()
        
        print("\n" + "-"*40)
        print("🎫 Creating simulated ticket...")
        print("-"*40)
        
        try:
            ticket_response = formatter.create_simulated_ticket(
                query=query,
                user_email=user_email,
                additional_description=additional_details
            )
            
            print(ticket_response)
            
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    while True:
        print("🎫 nQuiry Ticket Creation Demo")
        print("="*40)
        print("1. Run predefined demo scenarios")
        print("2. Show category mapping")
        print("3. Interactive demo")
        print("4. Exit")
        print()
        
        choice = input("Select an option (1-4): ").strip()
        
        if choice == '1':
            demo_ticket_creation()
        elif choice == '2':
            demo_category_mapping()
        elif choice == '3':
            interactive_demo()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-4.")
        
        print("\n" + "="*60 + "\n")