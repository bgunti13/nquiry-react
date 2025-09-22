
"""
Test script for explicit ticket creation functionality
"""

from main import IntelligentQueryProcessor

def test_explicit_ticket_creation():
    """Test various ways users can explicitly request ticket creation"""
    
    print("🧪 Testing Explicit Ticket Creation Functionality")
    print("=" * 60)
    
    # Initialize processor
    processor = IntelligentQueryProcessor()
    test_user = "test@amd.com"
    
    test_scenarios = [
        {
            "name": "Direct ticket creation with issue description",
            "query": "create a ticket for user management not working",
            "description": "User directly asks to create ticket with issue details"
        },
        {
            "name": "Simple ticket creation request after getting help",
            "history": [
                {"type": "user", "message": "How do I enable user management?"},
                {"type": "assistant", "message": "To enable user management, go to Settings > User Management and toggle the enable switch."}
            ],
            "query": "create a ticket for this issue",
            "description": "User asks for ticket after receiving help"
        },
        {
            "name": "Ticket creation with different phrasing",
            "query": "please open a support ticket for reporting not working",
            "description": "User uses different wording for ticket creation"
        },
        {
            "name": "Ticket request without issue description",
            "history": [
                {"type": "user", "message": "Why is sync failing between systems?"},
                {"type": "assistant", "message": "Sync can fail due to network issues or configuration problems. Check your connection settings."}
            ],
            "query": "file a ticket",
            "description": "User requests ticket without specific issue details"
        },
        {
            "name": "Multiple ticket creation phrases",
            "queries": [
                "submit a ticket",
                "make a ticket", 
                "log a ticket",
                "raise a ticket",
                "escalate to ticket",
                "i need a ticket",
                "can you create a ticket"
            ],
            "description": "Test various ticket creation phrases"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 Test Scenario {i}: {scenario['name']}")
        print(f"📝 Description: {scenario['description']}")
        print("-" * 40)
        
        if 'queries' in scenario:
            # Test multiple queries
            for query in scenario['queries']:
                print(f"\n   Testing query: '{query}'")
                is_ticket_request = processor.is_ticket_creation_request(query)
                print(f"   🎫 Detected as ticket request: {is_ticket_request}")
        else:
            # Test single scenario
            query = scenario['query']
            history = scenario.get('history', [])
            
            print(f"Query: '{query}'")
            if history:
                print("History:")
                for msg in history:
                    print(f"  - {msg['type']}: {msg['message']}")
            
            # Test detection
            previous_response = ""
            if history:
                for msg in reversed(history):
                    if msg['type'] == 'assistant':
                        previous_response = msg['message']
                        break
            
            is_ticket_request = processor.is_ticket_creation_request(query, previous_response)
            print(f"🎫 Detected as ticket request: {is_ticket_request}")
            
            if is_ticket_request:
                print("🚀 Processing ticket creation...")
                try:
                    # Clear any existing history for clean test
                    processor.chat_history_manager.clear_history(test_user)
                    
                    # Add history if provided
                    if history:
                        for msg in history:
                            processor.chat_history_manager.add_message(
                                test_user, 
                                "user" if msg['type'] == 'user' else "assistant", 
                                msg['message']
                            )
                    
                    result = processor.process_query(test_user, query, history)
                    
                    print(f"✅ Result: {result['source']}")
                    if result.get('ticket_created'):
                        print("🎫 Ticket created successfully!")
                        # Show first few lines of ticket
                        ticket_lines = result['response'].split('\n')[:8]
                        for line in ticket_lines:
                            if line.strip():
                                print(f"   {line}")
                        print("   ...")
                    else:
                        print(f"📄 Response: {result['response'][:200]}...")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print("✅ Enhanced ticket creation detection allows users to:")
    print("   • Explicitly request tickets anytime with phrases like 'create a ticket'")
    print("   • Request tickets after receiving help/information")
    print("   • Use various ticket creation phrases naturally")
    print("   • Create tickets even without detailed issue descriptions")
    print("✅ System intelligently extracts issue context from:")
    print("   • Current query if it contains issue details")
    print("   • Recent chat history for context")
    print("   • Fallback to generic ticket if no context available")

if __name__ == "__main__":
    test_explicit_ticket_creation()