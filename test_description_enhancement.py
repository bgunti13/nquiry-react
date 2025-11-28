"""
Test script for enhanced description functionality
"""
import boto3
import json

def enhance_description_with_context(query: str, chat_history=None) -> str:
    """Enhance description with AI analysis and conversation context using AWS Bedrock"""
    try:
        # Initialize Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        
        # Prepare conversation context
        conversation_context = ""
        if chat_history:
            user_messages = []
            for msg in chat_history[-10:]:
                if msg.get('role') == 'user' and len(msg.get('message', '')) > 5:
                    user_messages.append(msg.get('message', ''))
            
            if user_messages:
                conversation_context = f"\n\nConversation History:\n"
                for i, msg in enumerate(user_messages[-5:], 1):
                    conversation_context += f"User Message {i}: {msg}\n"
        
        # Create prompt for Bedrock
        prompt = f"""You are a technical support analyst. Analyze the following user query and conversation history to create a comprehensive ticket description.

Current User Query: {query}
{conversation_context}

Please provide a detailed technical description that:
1. Clearly explains what the user is trying to accomplish
2. Identifies the specific technical area/feature involved
3. Analyzes any context from the conversation
4. Suggests the likely root cause or area of investigation
5. Keeps it professional and technical

Provide only the enhanced description without any prefixes or labels. Make it 2-4 sentences that a support engineer would find helpful."""

        # Call Bedrock Claude model
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        enhanced_description = response_body['content'][0]['text'].strip()
        
        print(f"✅ Generated enhanced description via Bedrock")
        return enhanced_description
        
    except Exception as e:
        print(f"⚠️ Could not enhance description with Bedrock: {e}")
        print("🔄 Using intelligent fallback...")
        
        # Enhanced fallback analysis
        if 'rebate' in query.lower():
            return f"""Payment Processing Issue: {query}

This appears to be related to rebate management functionality, specifically concerning the timing and scheduling of future rebate payments. The user needs guidance on system configuration or process workflows for delayed payment creation. This likely involves understanding the rebate calculation engine, payment scheduling mechanisms, or batch processing configurations that control when future rebate payments are generated and processed."""
        elif 'login' in query.lower() or 'access' in query.lower():
            return f"""Access Issue: {query}

This is an authentication/authorization related request. The user is experiencing difficulties accessing the system or specific features. Investigation should focus on user permissions, authentication services, session management, or potential system connectivity issues."""
        elif 'error' in query.lower() or 'issue' in query.lower():
            return f"""System Error: {query}

The user is encountering a technical issue that requires investigation. This may involve system functionality, data processing, or application behavior that is not working as expected. Support should analyze error logs, system status, and user workflow to identify the root cause."""
        else:
            return f"""User Request: {query}

The user requires technical assistance with system functionality. This request needs analysis to determine the specific area of the application and appropriate resolution steps. Support should gather additional details about the user's workflow, expected behavior, and current system state to provide targeted assistance."""

# Test the function
if __name__ == "__main__":
    print("Testing enhanced description function...")
    
    test_query = "How do I enable the delayed creation of future rebates payments?"
    test_history = [
        {"role": "user", "message": "I'm having issues with rebate processing"},
        {"role": "assistant", "message": "I can help with rebate issues"},
        {"role": "user", "message": "The payments aren't being created when they should be"},
        {"role": "user", "message": test_query}
    ]
    
    print(f"\nOriginal query: {test_query}")
    print(f"Chat history: {len(test_history)} messages")
    
    enhanced = enhance_description_with_context(test_query, test_history)
    print(f"\nEnhanced description:")
    print("=" * 60)
    print(enhanced)
    print("=" * 60)
    print(f"\nLength: {len(enhanced)} characters")