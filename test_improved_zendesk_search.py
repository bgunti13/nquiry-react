"""
Test the improved Zendesk search with keyword-based matching
"""

from tools.zendesk_tool import ZendeskTool

def test_improved_zendesk_search():
    """Test the improved keyword-based Zendesk search"""
    print("🧪 Testing Improved Zendesk Search")
    print("=" * 50)
    
    try:
        zendesk_tool = ZendeskTool()
        
        # Test queries that should find results
        test_queries = [
            "upload file workbench",
            "workbench",
            "upload",
            "file",
            "validation",
            "report",
            "error"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            tickets = zendesk_tool.search_tickets(query, organization=None, limit=5)
            print(f"   Found {len(tickets)} tickets")
            
            if tickets:
                print(f"   ✅ SUCCESS - Top results:")
                for i, ticket in enumerate(tickets[:2]):
                    title = ticket.get('summary', 'No title')[:80]
                    print(f"      {i+1}. {ticket.get('key', 'No ID')}: {title}...")
            else:
                print(f"   ⚠️  No results for '{query}'")
                
        print("\n" + "=" * 50)
        print("✅ Keyword-based search test completed")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_zendesk_search()