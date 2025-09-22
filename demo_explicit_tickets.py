
"""
Simple demonstration of enhanced ticket creation functionality
"""

from main import IntelligentQueryProcessor

def demo_ticket_creation():
    """Demonstrate the enhanced ticket creation functionality"""
    
    print("🎫 Enhanced Ticket Creation Demo")
    print("=" * 50)
    
    processor = IntelligentQueryProcessor()
    
    # Test various ticket creation phrases
    test_phrases = [
        "create a ticket for user management not working",
        "please create a ticket",
        "submit a support ticket",
        "open a ticket for this issue",
        "make a ticket",
        "file a ticket",
        "can you create a ticket for me"
    ]
    
    print("🔍 Testing ticket creation detection:")
    print("-" * 30)
    
    for phrase in test_phrases:
        is_detected = processor.is_ticket_creation_request(phrase)
        status = "✅ DETECTED" if is_detected else "❌ NOT DETECTED"
        print(f"{status}: '{phrase}'")
    
    print("\n🚀 Full Workflow Demo:")
    print("-" * 30)
    
    # Simulate a real interaction
    user_email = "admin@amd.com"
    
    # First, user asks a question and gets help
    print("👤 User: How do I configure user sync?")
    print("🤖 Bot: [provides configuration steps]")
    print()
    
    # Then user explicitly requests ticket creation
    print("👤 User: create a ticket for this sync issue")
    
    # Process the ticket request
    try:
        result = processor.process_query(user_email, "create a ticket for sync configuration issue")
        
        if result.get('source') == 'TICKET_CREATION':
            print("🎫 TICKET CREATION INITIATED")
            print()
            
            # Show key parts of the response
            response_lines = result['response'].split('\n')
            for line in response_lines[:15]:  # Show first 15 lines
                if line.strip():
                    print(line)
            print("...")
            print()
            print("✅ Ticket created successfully!")
        else:
            print(f"❌ Unexpected result: {result.get('source')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Key Enhancement:")
    print("Users can now explicitly request ticket creation")
    print("at any time, even after receiving help!")

if __name__ == "__main__":
    demo_ticket_creation()