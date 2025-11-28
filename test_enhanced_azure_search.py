# -*- coding: utf-8 -*-
"""
Test Enhanced Azure Blob Content Search
Tests the new content extraction and search capabilities
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_enhanced_azure_search():
    """Test the enhanced Azure Blob search with content extraction"""
    print("🔧 Testing Enhanced Azure Blob Content Search")
    print("=" * 60)
    
    try:
        from tools.azure_blob_tool import AzureBlobSharePointTool
        
        # Initialize the enhanced tool
        blob_tool = AzureBlobSharePointTool()
        
        # Test authentication
        if not blob_tool.authenticate():
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
        
        # Test searches for workbench-related content
        test_queries = [
            "upload file workbench",
            "workbench upload",
            "how to upload",
            "file upload procedure",
            "workbench"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            print("-" * 40)
            
            try:
                results = blob_tool.search_documents(query)
                
                if results:
                    print(f"✅ Found {len(results)} results")
                    
                    # Show top 3 results
                    for i, doc in enumerate(results[:3], 1):
                        print(f"\n📄 Result {i}:")
                        print(f"   📁 Name: {doc.get('name', 'Unknown')}")
                        print(f"   🎯 Match Type: {doc.get('match_type', 'Unknown')}")
                        print(f"   📊 Relevance: {doc.get('relevance_score', 0):.2f}")
                        print(f"   📏 Size: {doc.get('size', 0)} bytes")
                        
                        # Show content preview if available
                        content = doc.get('content', '')
                        if content:
                            preview = content.replace('\n', ' ').strip()[:200]
                            print(f"   📖 Content: {preview}...")
                        else:
                            print(f"   📖 Content: [No content extracted]")
                    
                    if len(results) > 3:
                        print(f"\n   ... and {len(results) - 3} more results")
                        
                else:
                    print("❌ No results found")
                    
            except Exception as e:
                print(f"❌ Search error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Enhanced Azure Blob search test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure Azure Blob tool is properly configured")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_enhanced_azure_search()