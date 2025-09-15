"""
Response formatter module for creating user-friendly responses
"""

import boto3
import json
import os
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from config import AWS_REGION, BEDROCK_MODEL

load_dotenv()

class ResponseFormatter:
    """
    Formats search results into user-friendly responses using LLM
    """
    
    def __init__(self):
        self.bedrock_client = self._create_bedrock_client()
        self.model_id = BEDROCK_MODEL
    
    def _create_bedrock_client(self):
        """Create AWS Bedrock client"""
        try:
            session = boto3.Session(
                aws_access_key_id=os.getenv('aws_access_key_id'),
                aws_secret_access_key=os.getenv('aws_secret_access_key'),
                aws_session_token=os.getenv('aws_session_token'),
                region_name=AWS_REGION
            )
            return session.client('bedrock-runtime')
        except Exception as e:
            print(f"Error creating Bedrock client: {e}")
            return None
    
    def format_search_results(self, query: str, results: List[Tuple[Dict, float]], source: str, context: str = "") -> str:
        """
        Format search results into a user-friendly response
        
        Args:
            query: Original user query
            results: List of (document, similarity_score) tuples
            source: Source name (JIRA, CONFLUENCE, MINDTOUCH)
            context: Previous conversation context
            
        Returns:
            Formatted response string
        """
        if not results:
            return self._create_no_results_response(query, source)
        
        if not self.bedrock_client:
            return self._create_simple_response(query, results, source)
        
        try:
            # Prepare context from search results
            content_context = self._prepare_context(results, source)
            
            # Create prompt for LLM formatting (include conversation context)
            prompt = self._create_formatting_prompt(query, content_context, source, context)
            
            # Get LLM response
            formatted_response = self._get_llm_response(prompt)
            
            if formatted_response:
                return formatted_response
            else:
                return self._create_simple_response(query, results, source)
                
        except Exception as e:
            print(f"Error formatting response: {e}")
            return self._create_simple_response(query, results, source)
    
    def _prepare_context(self, results: List[Tuple[Dict, float]], source: str) -> str:
        """Prepare context string from search results with enhanced resolution info"""
        context_parts = []
        
        for i, (doc, score) in enumerate(results[:5], 1):  # Limit to top 5 results
            title = doc.get('title', 'Untitled')
            content = doc.get('content', doc.get('summary', doc.get('description', '')))
            
            # For JIRA tickets, prioritize resolution and comments
            if source == 'JIRA':
                description = doc.get('description', '')
                resolution = doc.get('resolution', '')
                comments = doc.get('comments', [])
                
                # Build comprehensive content for JIRA
                jira_content = f"DESCRIPTION: {description[:300]}..." if len(description) > 300 else f"DESCRIPTION: {description}"
                
                # Add resolution steps if available
                if resolution:
                    jira_content += f"\n\nRESOLUTION: {resolution}"
                
                # Add recent comments that might contain solutions
                if comments:
                    jira_content += "\n\nRECENT COMMENTS WITH SOLUTIONS:"
                    for comment in comments[-3:]:  # Last 3 comments
                        comment_body = comment.get('body', '')
                        if any(keyword in comment_body.lower() for keyword in ['solution', 'resolved', 'fix', 'steps', 'workaround']):
                            jira_content += f"\n- {comment.get('author', 'User')}: {comment_body[:200]}..."
                
                content = jira_content
            elif source == 'MINDTOUCH':
                # For MindTouch LLM responses, preserve full content as they contain comprehensive solutions
                # Don't truncate MindTouch content since it's already curated LLM responses
                pass  # Keep full content as-is
            else:
                # Truncate content if too long for other sources (Confluence)
                if len(content) > 500:
                    content = content[:500] + "..."
            
            context_part = f"Result {i} (Relevance: {score:.2f}):\nTitle: {title}\nContent: {content}\n"
            
            # Add source-specific metadata
            if source == 'JIRA':
                context_part += f"Issue Key: {doc.get('key', 'N/A')}\n"
                context_part += f"Status: {doc.get('status', 'N/A')}\n"
                context_part += f"Priority: {doc.get('priority', 'N/A')}\n"
                if doc.get('resolution_date'):
                    context_part += f"Resolution Date: {doc.get('resolution_date', 'N/A')}\n"
            elif source == 'CONFLUENCE':
                context_part += f"Page ID: {doc.get('id', 'N/A')}\n"
                context_part += f"Space: {doc.get('space', 'N/A')}\n"
            elif source == 'MINDTOUCH':
                context_part += f"Page ID: {doc.get('id', 'N/A')}\n"
                context_part += f"Path: {doc.get('path', 'N/A')}\n"
            
            context_parts.append(context_part)
        
        return "\n" + "-"*50 + "\n".join(context_parts)
    
    def _create_formatting_prompt(self, query: str, content_context: str, source: str, conversation_context: str = "") -> str:
        """Create prompt for LLM to format the response"""
        # Check query type for specialized formatting
        is_how_to_query = any(word in query.lower() for word in ['how to', 'how do i', 'enable', 'configure', 'setup', 'steps'])
        is_issue_query = any(word in query.lower() for word in ['not working', 'error', 'issue', 'problem', 'failing', 'not syncing', 'broken'])
        
        base_prompt = f"""
You are a helpful assistant that formats search results into clear, actionable responses.

{f"Conversation Context (previous messages):\n{conversation_context}\n" if conversation_context else ""}

Current User Query: {query}
Source: {source}
Search Results: {content_context}

IMPORTANT: Only use information that DIRECTLY answers the user's specific query. If this is a follow-up question, consider the conversation context to provide a relevant answer. Ignore content that is not relevant to the exact question asked.

Please create a focused, well-structured response that:"""

        if source == 'JIRA' and is_issue_query:
            # Special handling for JIRA issue resolution queries
            base_prompt += """
1. FOCUS ON RESOLUTION STEPS - Look for and prioritize any resolution information, workarounds, or solution steps mentioned in comments or resolution fields
2. EXTRACT ACTIONABLE SOLUTIONS - Present specific steps taken to resolve similar issues, including:
   - Root cause analysis if mentioned
   - Specific configuration changes made
   - Commands run or procedures followed
   - Settings modified or values changed
   - Any workarounds or temporary fixes applied
3. Use numbered steps for any resolution procedures found
4. Include technical details like specific error messages, file paths, or system settings mentioned
5. If the issue is resolved, clearly state the final resolution and any preventive measures
6. If the issue is still open, mention the current status and any ongoing investigation steps
7. PRIORITIZE the most relevant ticket that matches the user's exact issue
8. Format as: **Problem Description** → **Root Cause** → **Resolution Steps** → **Result/Status**

Focus on providing actionable solutions rather than just describing the problem."""
        elif source == 'MINDTOUCH' or 'MindTouch LLM' in str(content_context):
            # Special handling for MindTouch LLM responses - they are pre-curated comprehensive solutions
            base_prompt += """
1. PRIORITIZE MINDTOUCH LLM RESPONSES - MindTouch responses are comprehensive, expert-curated solutions that should be used as the primary answer
2. EXTRACT AND PRESENT THE FULL SOLUTION - Present all the step-by-step instructions, configuration details, and resolution steps exactly as provided
3. Maintain the original structure and formatting of numbered steps, bullet points, and sections
4. Include all technical details like specific settings, field names, navigation paths, and values mentioned
5. Do NOT summarize or truncate the MindTouch response - present it in full as it's already optimized
6. If multiple sources are present, lead with the MindTouch response as the authoritative answer
7. Format clearly with proper headers and step numbering for easy following
8. IGNORE other sources if MindTouch provides a complete solution to avoid confusion

MindTouch responses are expert-level, comprehensive solutions - use them as the definitive answer."""
        elif (source == 'MULTI' or 'fallback' in str(content_context).lower()) and is_issue_query:
            # Special handling for multi-source fallback searches with issues
            base_prompt += """
1. PRIORITIZE THE HIGHEST-SCORING MINDTOUCH RESULTS - If MindTouch LLM responses are present, use them as the primary solution
2. LOOK FOR COMPREHENSIVE SOLUTIONS - Focus on results that provide complete resolution steps rather than just problem descriptions
3. EXTRACT ACTIONABLE RESOLUTION STEPS - Present specific troubleshooting and resolution procedures from the most relevant sources
4. Use clear step-by-step formatting with numbered instructions
5. Include technical details like configuration changes, settings, and system commands
6. Combine complementary information from multiple sources only if it enhances the solution
7. IGNORE results that just restate the problem without providing solutions
8. Format as: **Solution Steps** → **Technical Details** → **Verification**

Focus on providing the most complete and actionable solution from the available sources."""
        elif is_how_to_query:
            # For configuration/how-to queries, emphasize step-by-step instructions
            base_prompt += """
1. FOCUS ONLY ON THE MOST RELEVANT DOCUMENT - Use primarily the highest-scoring result that directly answers the query
2. EXTRACT SPECIFIC STEP-BY-STEP INSTRUCTIONS - Present the actual configuration steps, settings, or procedures from the most relevant documentation
3. Use numbered steps with clear, actionable instructions (e.g., "1. Navigate to X", "2. Click Y", "3. Change setting Z to value W")
4. Include specific setting names, field names, configuration paths, and values mentioned in the documentation
5. Organize information in a logical sequence that users can follow
6. Mention any prerequisites, warnings, or post-configuration steps (like application restarts)
7. Use clear formatting with headers, bullet points, and emphasis for important details
8. IGNORE information from other documents that doesn't directly relate to the specific question asked

Focus on being actionable and specific rather than comprehensive. Quality over quantity."""
        else:
            # For regular queries, use the original format
            base_prompt += """
1. PRIORITIZE THE MOST RELEVANT INFORMATION - Focus on content that directly addresses the user's query
2. Filter out information that doesn't specifically relate to the question asked
3. Summarize only the most relevant findings from the highest-scoring documents
4. Organize the information clearly with proper formatting
5. Include specific details like issue keys, page titles, or document paths where relevant
6. Use bullet points or numbered lists for better readability
7. Maintain a helpful and professional tone
8. AVOID including tangential or loosely related information

Focus on relevance and precision rather than completeness."""

        base_prompt += """

CRITICAL: When multiple search results are provided, focus primarily on the most relevant and highest-scoring documents. Do NOT try to summarize all documents - instead, extract only the information that directly answers the user's specific question. If a document doesn't contain relevant information for the exact query, ignore it completely.

Response:"""
        
        return base_prompt
    
    def _get_llm_response(self, prompt: str) -> Optional[str]:
        """Get formatted response from LLM"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            
            return None
            
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return None
    
    def _create_simple_response(self, query: str, results: List[Tuple[Dict, float]], source: str) -> str:
        """Create a simple formatted response without LLM"""
        response_parts = [
            f"🔍 Search Results for: '{query}'",
            f"📂 Source: {source}",
            f"📊 Found {len(results)} relevant result(s)\n"
        ]
        
        for i, (doc, score) in enumerate(results, 1):
            title = doc.get('title', 'Untitled')
            content = doc.get('content', doc.get('summary', doc.get('description', '')))
            
            # Truncate content
            if len(content) > 300:
                content = content[:300] + "..."
            
            result_section = [
                f"📄 Result {i} (Relevance: {score:.2f})",
                f"Title: {title}",
                f"Content: {content}"
            ]
            
            # Add source-specific info
            if source == 'JIRA':
                result_section.append(f"Issue Key: {doc.get('key', 'N/A')}")
                result_section.append(f"Status: {doc.get('status', 'N/A')}")
            elif source == 'CONFLUENCE':
                result_section.append(f"Page ID: {doc.get('id', 'N/A')}")
            elif source == 'MINDTOUCH':
                result_section.append(f"Path: {doc.get('path', 'N/A')}")
            
            response_parts.append("\n".join(result_section))
            response_parts.append("-" * 50)
        
        return "\n".join(response_parts)
    
    def _create_no_results_response(self, query: str, source: str) -> str:
        """Create response when no results are found"""
        return f"""
🔍 Search Results for: '{query}'
📂 Source: {source}

❌ No relevant information found in {source}.

This could mean:
• The information might be in a different knowledge source
• The query might need to be rephrased
• The information might not exist in our knowledge base

Would you like to:
1. Try searching in a different source
2. Rephrase your query
3. Create a support ticket for assistance
"""
    
    def format_multi_source_results(self, query: str, all_results: Dict[str, List[Tuple[Dict, float]]]) -> str:
        """
        Format results from multiple sources
        
        Args:
            query: Original user query
            all_results: Dictionary with source names as keys and results as values
            
        Returns:
            Formatted multi-source response
        """
        if not all_results:
            return f"❌ No relevant information found for query: '{query}'"
        
        response_parts = [
            f"🔍 Comprehensive Search Results for: '{query}'",
            f"📊 Searched across {len(all_results)} source(s)\n"
        ]
        
        # Sort sources by total relevance score
        sorted_sources = sorted(
            all_results.items(),
            key=lambda x: sum(score for _, score in x[1]),
            reverse=True
        )
        
        for source, results in sorted_sources:
            if results:
                source_response = self.format_search_results(query, results, source)
                response_parts.append(f"📂 {source} Results:")
                response_parts.append(source_response)
                response_parts.append("="*60)
        
        return "\n".join(response_parts)