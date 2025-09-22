"""
Test script for the enhanced ticket creation with field collection
"""

from response_formatter import ResponseFormatter
from main import IntelligentQueryProcessor

def test_field_collection():
    """Test the field collection functionality"""
    
    print("🧪 Testing Field Collection for Ticket Creation")
    print("="*60)
    
    formatter = ResponseFormatter()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "MNHT Ticket - Missing Fields",
            "query": "User management is not working in Model N Hi-Tech",
            "user_email": "admin@amd.com",
            "expected_fields": ["area", "affected_version", "reported_environment"]
        },
        {
            "name": "MNLS Ticket - Missing Fields", 
            "query": "Configuration issues with Novartis system",
            "user_email": "support@novartis.com",
            "expected_fields": ["area", "affected_version", "reported_environment"]
        },
        {
            "name": "NOC Ticket - Only Description Required",
            "query": "Need access to monitoring dashboard",
            "user_email": "ops@company.com",
            "expected_fields": []  # Only description required
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test Scenario {i}: {scenario['name']}")
        print("-" * 50)
        
        try:
            # Test initial ticket creation attempt (should prompt for fields if needed)
            print(f"🔄 Attempting to create ticket without collected fields...")
            result = formatter.create_simulated_ticket(
                query=scenario['query'],
                user_email=scenario['user_email']
            )
            
            print(f"📤 Result:\n{result[:300]}...")
            
            if "Additional Information Required" in result:
                print("✅ Correctly identified missing fields and prompted user")
                
                # Test field parsing
                print("\n🧪 Testing field parsing...")
                test_responses = [
                    "Area: User Management\nAffected Version: 2.3.1\nReported Environment: Production",
                    "area: configuration\nversion: 1.2.3\nenvironment: staging",
                    "User Management area, version 2.1.0, production environment"
                ]
                
                for response in test_responses:
                    print(f"\n📝 Test Response: {response}")
                    parsed_fields = formatter.parse_field_response(response)
                    print(f"🔍 Parsed Fields: {parsed_fields}")
                    
                    # Try creating ticket with parsed fields
                    if parsed_fields:
                        final_result = formatter.create_simulated_ticket(
                            query=scenario['query'],
                            user_email=scenario['user_email'],
                            collected_fields=parsed_fields
                        )
                        
                        if "Demo Ticket Created Successfully" in final_result:
                            print("✅ Successfully created ticket with collected fields")
                            break
                        else:
                            print("⚠️ Still missing some required fields")
            else:
                print("✅ Ticket created without additional fields (as expected)")
                
        except Exception as e:
            print(f"❌ Error in test scenario: {e}")
        
        print("\n" + "="*60)

def test_integrated_field_collection():
    """Test the integrated field collection workflow"""
    
    print("\n🧪 Testing Integrated Field Collection Workflow")
    print("="*60)
    
    processor = IntelligentQueryProcessor()
    
    # Simulate the complete workflow
    test_cases = [
        {
            "name": "MNHT Product Support with Field Collection",
            "user_email": "admin@amd.com",
            "steps": [
                ("User management is broken in our Model N system", "initial_query"),
                ("yes", "ticket_creation_request"),
                ("Area: User Management\nAffected Version: 2.3.1\nReported Environment: Production", "field_information")
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Test Case: {test_case['name']}")
        print("-" * 50)
        
        user_email = test_case['user_email']
        chat_history = []
        
        for step_query, step_type in test_case['steps']:
            print(f"\n💬 User ({step_type}): {step_query}")
            
            try:
                # Process the query
                result = processor.process_query(user_email, step_query, chat_history)
                
                response = result.get('response', 'No response')
                print(f"🤖 Bot: {response[:200]}...")
                
                # Update chat history for next step
                chat_history = result.get('chat_history', [])
                
                if result.get('ticket_created'):
                    print("✅ Ticket creation completed!")
                    break
                elif "Additional Information Required" in response:
                    print("📝 System requesting additional fields")
                elif result.get('source') == 'FIELD_COLLECTION':
                    print("📝 Processing field information")
                
            except Exception as e:
                print(f"❌ Error processing step: {e}")
                break
        
        print("\n" + "="*60)

def test_field_parsing():
    """Test various field parsing formats"""
    
    print("\n🧪 Testing Field Parsing Formats")
    print("="*40)
    
    formatter = ResponseFormatter()
    
    test_inputs = [
        # Structured format
        "Area: User Management\nAffected Version: 2.3.1\nReported Environment: Production",
        
        # Casual format
        "area: configuration, version: 1.2.0, environment: staging",
        
        # Free text format
        "The issue is in User Management with version 2.1.5 in production",
        
        # Minimal format
        "version 1.0.0 production",
        
        # Mixed format
        "Area: Reporting\nversion 3.2.1\nenv: development"
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n📝 Test Input {i}: {test_input}")
        parsed = formatter.parse_field_response(test_input)
        print(f"🔍 Parsed: {parsed}")

if __name__ == "__main__":
    while True:
        print("🧪 Field Collection Test Suite")
        print("="*40)
        print("1. Test field collection prompts")
        print("2. Test integrated workflow") 
        print("3. Test field parsing")
        print("4. Run all tests")
        print("5. Exit")
        
        choice = input("\nSelect test (1-5): ").strip()
        
        if choice == "1":
            test_field_collection()
        elif choice == "2":
            test_integrated_field_collection()
        elif choice == "3":
            test_field_parsing()
        elif choice == "4":
            test_field_parsing()
            test_field_collection()
            test_integrated_field_collection()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")