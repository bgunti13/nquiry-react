"""
Test script to demonstrate the integrated ticket creation functionality
"""

from main import IntelligentQueryProcessor
import json

def test_integrated_ticket_creation():
    """Test the integrated ticket creation flow"""
    
    print("🧪 Testing Integrated Ticket Creation Flow")
    print("="*60)
    
    # Initialize the processor
    processor = IntelligentQueryProcessor()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Database Issue Leading to Ticket Creation",
            "user_email": "admin@amd.com",
            "initial_query": "Database is not syncing properly in production",
            "follow_up": "yes"
        },
        {
            "name": "Access Request Leading to Ticket Creation", 
            "user_email": "support@company.com",
            "initial_query": "Need access to monitoring system",
            "follow_up": "yes please"
        },
        {
            "name": "Product Support Query (Novartis)",
            "user_email": "helpdesk@novartis.com", 
            "initial_query": "How to configure user roles in Model N Life Sciences",
            "follow_up": "create ticket"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print("-" * 50)
        
        user_email = test_case['user_email']
        initial_query = test_case['initial_query']
        follow_up = test_case['follow_up']
        
        print(f"👤 User: {user_email}")
        print(f"💬 Initial Query: {initial_query}")
        
        try:
            # Process the initial query
            print("\n🔄 Processing initial query...")
            initial_response = processor.process_query(user_email, initial_query)
            
            print(f"📤 Bot Response: {initial_response.get('response', 'No response')[:200]}...")
            
            # Simulate the follow-up response for ticket creation
            print(f"\n💬 User Follow-up: {follow_up}")
            print("🔄 Processing follow-up...")
            
            # Get chat history for context
            chat_history = initial_response.get('chat_history', [])
            
            # Process the follow-up (ticket creation request)
            follow_up_response = processor.process_query(user_email, follow_up, chat_history)
            
            if follow_up_response.get('ticket_created'):
                print("✅ Ticket creation successful!")
                print(f"📄 Response type: {follow_up_response.get('source')}")
                print(f"🎫 Ticket details: {follow_up_response.get('response', '')[:300]}...")
            else:
                print("❌ Ticket creation failed or not detected")
                print(f"📄 Response: {follow_up_response.get('response', '')[:200]}...")
                
        except Exception as e:
            print(f"❌ Error in test case: {e}")
        
        print("\n" + "="*60)
        
        if i < len(test_cases):
            input("Press Enter to continue to next test case...")

def test_ticket_detection():
    """Test the ticket creation detection logic"""
    
    print("\n🧪 Testing Ticket Creation Detection Logic")
    print("="*50)
    
    processor = IntelligentQueryProcessor()
    
    test_queries = [
        ("yes", "Would you like me to create a support ticket?", True),
        ("sure", "Would you like me to create a support ticket?", True),
        ("create ticket", "", True),
        ("no thanks", "Would you like me to create a support ticket?", False),
        ("what is the weather", "", False),
        ("okay", "create a support ticket for assistance", True),
        ("proceed", "Would you like to create a ticket?", True)
    ]
    
    print("Testing query detection:")
    for query, previous_response, expected in test_queries:
        result = processor.is_ticket_creation_request(query, previous_response)
        status = "✅" if result == expected else "❌"
        print(f"{status} Query: '{query}' | Previous: '{previous_response[:30]}...' | Expected: {expected} | Got: {result}")

if __name__ == "__main__":
    print("🎫 nQuiry Integrated Ticket Creation Test Suite")
    print("="*60)
    
    while True:
        print("\nSelect test to run:")
        print("1. Test integrated ticket creation flow")
        print("2. Test ticket detection logic")
        print("3. Run both tests")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            test_integrated_ticket_creation()
        elif choice == "2":
            test_ticket_detection()
        elif choice == "3":
            test_ticket_detection()
            test_integrated_ticket_creation()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-4.")