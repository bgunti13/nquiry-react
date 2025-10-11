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
    def get_required_fields_for_query(self, query: str, user_email: str = "") -> List[str]:
        """
        Given a query and user email, determine the ticket category and return the required field names to be requested from the customer.
        """
        try:
            import json
            config_path = os.path.join(os.path.dirname(__file__), 'ticket_mapping_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            category = self._determine_ticket_category(query, user_email, config)
            # Only return fields that should be requested from the customer
            if category in ['MNHT', 'MNLS']:
                return ['description', 'area', 'affected_version', 'reported_environment']
            elif category == 'NOC':
                return ['description']
            elif category == 'COPS':
                return ['description']
            else:
                # Default: all required fields
                required_fields = config['ticket_categories'][category]['required_fields']
                return list(required_fields.keys())
        except Exception as e:
            print(f"Error in get_required_fields_for_query: {e}")
            return []
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
        try:
            if not results:
                return self._create_no_results_response(query, source)

            # Ensure results is a list of tuples with two elements each
            if not isinstance(results, list) or not all(
                isinstance(item, tuple) and len(item) == 2 for item in results
            ):
                raise ValueError("results must be a list of (document, similarity_score) tuples.")

            if not self.bedrock_client:
                return self._create_simple_response(query, results, source)
            
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
        
        print(f"🔍 _prepare_context: Processing {len(results)} results for source {source}")
        
        for i, (doc, score) in enumerate(results[:5], 1):  # Limit to top 5 results
            title = doc.get('title', 'Untitled')
            content = doc.get('content', doc.get('summary', doc.get('description', '')))
            
            print(f"📄 Result {i}: Title='{title}', Content length={len(content) if content else 0}")
            print(f"📝 Content preview: {content[:100]}..." if content else "❌ No content found")
            
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
                    relevant_comments_found = 0
                    for comment in comments[-5:]:  # Last 5 comments
                        comment_body = comment.get('body', '')
                        # More inclusive keyword list for solution-related content
                        solution_keywords = ['solution', 'resolved', 'fix', 'steps', 'workaround', 'issue', 'problem', 
                                           'troubleshoot', 'error', 'sync', 'account', 'resolve', 'cause', 'root',
                                           'investigation', 'found', 'discovered', 'update', 'change', 'config']
                        
                        if any(keyword in comment_body.lower() for keyword in solution_keywords) or len(comment_body) > 50:
                            jira_content += f"\n- {comment.get('author', 'User')}: {comment_body[:300]}..."
                            relevant_comments_found += 1
                    
                    # If no "relevant" comments found, include all recent comments anyway
                    if relevant_comments_found == 0:
                        jira_content += "\n\nALL RECENT COMMENTS:"
                        for comment in comments[-3:]:  # Last 3 comments
                            comment_body = comment.get('body', '')
                            if comment_body:
                                jira_content += f"\n- {comment.get('author', 'User')}: {comment_body[:300]}..."
                
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

**FORMATTING REQUIREMENTS:**
- DO NOT include any raw search result references like "(Result 1)", "(Result 2)" in your response
- DO NOT include bullet points that start with raw search data like "- New Salesforce accounts do not sync..."  
- DO NOT include phrases like "Based on the provided search results" or "The key issue appears to be"
- DO NOT show internal search result formatting or citations
- Provide ONLY a clean, comprehensive response that directly answers the user's question
- Write as if you are explaining the solution directly, not analyzing search results

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
    
    def format_multi_source_results(self, query: str, all_results: Dict[str, List[Tuple[Dict, float]]], context: str = "") -> str:
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
                source_response = self.format_search_results(query, results, source, context)
                response_parts.append(f"📂 {source} Results:")
                response_parts.append(source_response)
                response_parts.append("="*60)
        
        return "\n".join(response_parts)
    
    def create_simulated_ticket(self, query: str, user_email: str = "", additional_description: str = "", collected_fields: Dict = None) -> str:
        """
        Create a simulated ticket based on the query and return ticket details as text
        
        Args:
            query: Original user query
            user_email: User's email to determine customer domain
            additional_description: Additional details provided by user
            collected_fields: Dictionary of required fields collected from user
            
        Returns:
            Text document with ticket details for demo purposes
        """
        try:
            # Load ticket mapping configuration
            import json
            import os
            from datetime import datetime
            
            config_path = os.path.join(os.path.dirname(__file__), 'ticket_mapping_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Determine ticket category based on query and user domain
            category = self._determine_ticket_category(query, user_email, config)
            
            # Get customer domain from email
            customer_domain = self._extract_customer_domain(user_email)
            
            # Check if we have all required fields
            required_fields = config['ticket_categories'][category]['required_fields']
            missing_fields = []
            
            # If collected_fields is not provided, we need to collect them
            if not collected_fields:
                collected_fields = {}
            
            # Check which required fields are missing
            for field_name, field_description in required_fields.items():
                if field_name == 'description':
                    # Description can be auto-filled from query
                    collected_fields[field_name] = query
                elif field_name not in collected_fields or not collected_fields[field_name]:
                    missing_fields.append((field_name, field_description))
            
            # If we have missing fields, return a field collection prompt
            if missing_fields:
                return self._create_field_collection_prompt(category, missing_fields, query, user_email)
            
            # Generate ticket data with collected fields
            ticket_data = self._generate_ticket_data_with_fields(
                query, category, customer_domain, additional_description, config, collected_fields
            )
            
            # Create ticket document
            ticket_document = self._create_ticket_document(ticket_data, category)
            
            # Save ticket to file for demo
            ticket_filename = self._save_ticket_to_file(ticket_document, category, customer_domain)
            
            return f"""✅ **Demo Ticket Created Successfully!**

📁 **Ticket File:** `{ticket_filename}`

{ticket_document}

📝 **Note:** This is a simulated ticket for demonstration purposes. In a production environment, this would be created in the actual ticketing system."""
            
        except Exception as e:
            return f"❌ Error creating simulated ticket: {str(e)}"
    
    def _create_field_collection_prompt(self, category: str, missing_fields: List[Tuple[str, str]], query: str, user_email: str) -> str:
        """Create a prompt to collect missing required fields from the user"""
        
        prompt_lines = [
            f"🎫 **Creating {category} Support Ticket**",
            "",
            f"📋 **Original Query:** {query}",
            f"👤 **Customer:** {self._extract_customer_domain(user_email)}",
            "",
            "📝 **Additional Information Required**",
            "To create your support ticket, please provide the following details:",
            ""
        ]
        
        for i, (field_name, field_description) in enumerate(missing_fields, 1):
            field_display = field_name.replace('_', ' ').title()
            prompt_lines.append(f"**{i}. {field_display}:** {field_description}")
            if "(Optional)" in field_description:
                prompt_lines.append(f"   ↳ *This field is optional - you can leave it blank*")
            prompt_lines.append("")
        
        prompt_lines.extend([
            "💡 **How to provide this information:**",
            "Please respond with your details in this format:",
            ""
        ])
        
        # Create example format
        example_format = []
        for field_name, field_description in missing_fields:
            field_display = field_name.replace('_', ' ').title()
            if field_name == 'area':
                example_format.append(f"• **{field_display}:** User Management")
            elif field_name == 'affected_version':
                example_format.append(f"• **{field_display}:** 2.3.1")
            elif field_name == 'reported_environment':
                example_format.append(f"• **{field_display}:** Production (or leave blank)")
            else:
                example_format.append(f"• **{field_display}:** [Your response here]")
        
        prompt_lines.extend(example_format)
        prompt_lines.extend([
            "",
            "📤 **Example Response:**",
            "Area: User Management",
            "Affected Version: 2.3.1", 
            "Reported Environment: Production",
            "",
            "🔄 Once you provide this information, I'll create your support ticket immediately."
        ])
        
        return "\n".join(prompt_lines)
    
    def _determine_ticket_category(self, query: str, user_email: str, config: Dict) -> str:
        """Determine the appropriate ticket category based on query and user domain"""
        query_lower = query.lower()
        
        # Extract customer domain for MNHT/MNLS determination
        customer_domain = self._extract_customer_domain(user_email)
        
        # Check for specific category keywords
        categories = config['ticket_categories']
        
        # Check NOC keywords first
        for keyword in categories['NOC']['keywords']:
            if keyword.lower() in query_lower:
                return 'NOC'
        
        # Check COPS keywords
        for keyword in categories['COPS']['keywords']:
            if keyword.lower() in query_lower:
                return 'COPS'
        
        # Check CSP keywords
        for keyword in categories['CSP']['keywords']:
            if keyword.lower() in query_lower:
                return 'CSP'
        
        # Check customer-specific mappings
        customer_mappings = config.get('customer_mappings', {})
        if customer_domain in customer_mappings:
            return customer_mappings[customer_domain]
        
        # Check for company-specific keywords in query
        if 'amd' in query_lower:
            return 'MNHT'
        elif 'novartis' in query_lower:
            return 'MNLS'
        
        # Default fallback based on customer domain or MNHT
        return customer_mappings.get(customer_domain, config.get('default_category', 'MNHT'))
    
    def _extract_customer_domain(self, user_email: str) -> str:
        """Extract customer domain from user email"""
        if not user_email or '@' not in user_email:
            return 'unknown'
        
        domain = user_email.split('@')[1].lower()
        
        # Map common domain patterns to customer names
        domain_mappings = {
            'amd.com': 'amd',
            'novartis.com': 'novartis',
            'modeln.com': 'modeln'
        }
        
        # Check for exact domain match
        for email_domain, customer in domain_mappings.items():
            if domain == email_domain:
                return customer
        
        # Check for partial domain match
        for email_domain, customer in domain_mappings.items():
            if customer in domain:
                return customer
        
        return domain.split('.')[0]  # Return first part of domain
    
    def _generate_ticket_data_with_fields(self, query: str, category: str, customer_domain: str, additional_description: str, config: Dict, collected_fields: Dict) -> Dict:
        """Generate ticket data using collected required fields"""
        from datetime import datetime
        import hashlib
        
        category_config = config['ticket_categories'][category]
        
        # Generate ticket ID
        ticket_id = f"{category}-{hashlib.md5(query.encode()).hexdigest()[:6].upper()}"
        
        # Generate summary based on description
        summary = f"Support Request: {query[:80]}{'...' if len(query) > 80 else ''}"
        
        # Base ticket data
        ticket_data = {
            'ticket_id': ticket_id,
            'category': category,
            'query': query,
            'summary': summary,
            'description': collected_fields.get('description', query),
            'customer_domain': customer_domain,
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': 'nQuiry AI Assistant'
        }
        
        # Add collected required fields
        for field_name, field_value in collected_fields.items():
            if field_name != 'description':  # Description is already handled above
                ticket_data[field_name] = field_value
        
        # Add additional description if provided
        if additional_description:
            ticket_data['description'] += f"\n\nAdditional Details: {additional_description}"
        
        # Add category-specific populated fields
        populated_fields = category_config['populated_fields'].copy()
        
        # Replace dynamic values
        for field, value in populated_fields.items():
            if isinstance(value, str):
                if 'based on description' in value.lower():
                    populated_fields[field] = summary
                elif 'based on user domain' in value.lower():
                    populated_fields[field] = customer_domain
                elif 'based on customer organization' in value.lower():
                    # Get the actual organization name from customer role manager
                    from customer_role_manager import CustomerRoleMappingManager
                    customer_manager = CustomerRoleMappingManager()
                    customer_mapping = customer_manager.get_customer_mapping(f"{customer_domain}.com")
                    populated_fields[field] = customer_mapping.get('organization', customer_domain.upper())
                elif 'based on customer sheet mapping' in value.lower():
                    # Determine MNHT or MNLS based on customer sheet mapping
                    from customer_role_manager import CustomerRoleMappingManager
                    customer_manager = CustomerRoleMappingManager()
                    customer_mapping = customer_manager.get_customer_mapping(f"{customer_domain}.com")
                    sheet = customer_mapping.get('sheet', 'HT')
                    if sheet.upper() == 'LS':
                        populated_fields[field] = 'MNLS'
                    else:  # Default to HT/MNHT
                        populated_fields[field] = 'MNHT'
                elif category in ['COPS'] and field == 'support_projects':
                    # Determine MNHT or MNLS based on customer (legacy fallback)
                    if customer_domain == 'amd':
                        populated_fields[field] = 'MNHT'
                    elif customer_domain == 'novartis':
                        populated_fields[field] = 'MNLS'
                    else:
                        populated_fields[field] = 'MNHT'  # Default
        
        ticket_data.update(populated_fields)
        
        return ticket_data

    def parse_field_response(self, response: str) -> Dict[str, str]:
        """
        Parse user response to extract field values
        
        Args:
            response: User's response containing field information
            
        Returns:
            Dictionary of field names and values
        """
        fields = {}
        
        # Common field patterns to look for
        field_patterns = {
            'area': ['area:', 'area', 'affected area:', 'module:', 'component:'],
            'affected_version': ['version:', 'affected version:', 'version affected:', 'ver:', 'release:'],
            'reported_environment': ['environment:', 'env:', 'reported environment:', 'environment affected:']
        }
        
        response_lower = response.lower()
        lines = response.split('\n')
        
        # Try to parse structured format first (Field: Value)
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field_name = parts[0].strip().lower()
                    field_value = parts[1].strip()
                    
                    # Map common field names
                    for standard_field, patterns in field_patterns.items():
                        if any(pattern in field_name for pattern in patterns):
                            if field_value and field_value.lower() not in ['n/a', 'na', 'none', 'blank', '']:
                                fields[standard_field] = field_value
                            break
        
        # If no structured format, try to extract from free text
        if not fields:
            # Look for version numbers
            import re
            version_match = re.search(r'\b(\d+\.\d+(?:\.\d+)?)\b', response)
            if version_match:
                fields['affected_version'] = version_match.group(1)
            
            # Look for environment keywords
            env_keywords = ['production', 'prod', 'staging', 'test', 'development', 'dev', 'uat']
            for env in env_keywords:
                if env in response_lower:
                    fields['reported_environment'] = env.title()
                    break
            
            # For area, take the first meaningful phrase (this is more heuristic)
            words = response.split()
            if len(words) >= 2:
                # Look for phrases that might indicate an area
                area_indicators = ['user', 'management', 'access', 'reporting', 'configuration', 'sync', 'integration']
                for i, word in enumerate(words):
                    if word.lower() in area_indicators and i < len(words) - 1:
                        fields['area'] = f"{word} {words[i+1]}".title()
                        break
                
                # If no area found, use first two meaningful words
                if 'area' not in fields and len(words) >= 2:
                    meaningful_words = [w for w in words[:4] if len(w) > 2 and w.lower() not in ['the', 'and', 'for', 'with']]
                    if len(meaningful_words) >= 2:
                        fields['area'] = ' '.join(meaningful_words[:2]).title()
        
        return fields
        """Generate ticket data based on category and query"""
        from datetime import datetime
        import hashlib
        
        category_config = config['ticket_categories'][category]
        
        # Generate ticket ID
        ticket_id = f"{category}-{hashlib.md5(query.encode()).hexdigest()[:6].upper()}"
        
        # Generate summary based on description
        summary = f"Support Request: {query[:80]}{'...' if len(query) > 80 else ''}"
        
        # Base ticket data
        ticket_data = {
            'ticket_id': ticket_id,
            'category': category,
            'query': query,
            'summary': summary,
            'description': f"Original Query: {query}",
            'customer_domain': customer_domain,
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': 'nQuiry AI Assistant'
        }
        
        # Add additional description if provided
        if additional_description:
            ticket_data['description'] += f"\n\nAdditional Details: {additional_description}"
        
        # Add category-specific fields
        populated_fields = category_config['populated_fields'].copy()
        
        # Replace dynamic values
        for field, value in populated_fields.items():
            if isinstance(value, str):
                if 'based on description' in value.lower():
                    populated_fields[field] = summary
                elif 'based on user domain' in value.lower():
                    populated_fields[field] = customer_domain
                elif category in ['COPS'] and field == 'support_projects':
                    # Determine MNHT or MNLS based on customer
                    if customer_domain == 'amd':
                        populated_fields[field] = 'MNHT'
                    elif customer_domain == 'novartis':
                        populated_fields[field] = 'MNLS'
                    else:
                        populated_fields[field] = 'MNHT'  # Default
        
        ticket_data.update(populated_fields)
        
        return ticket_data
    
    def _create_ticket_document(self, ticket_data: Dict, category: str) -> str:
        """Create formatted ticket document"""
        doc_lines = [
            "="*60,
            f"🎫 DEMO TICKET - {category} CATEGORY",
            "="*60,
            "",
            f"📋 **Ticket ID:** {ticket_data['ticket_id']}",
            f"📅 **Created:** {ticket_data['created_date']}",
            f"👤 **Created By:** {ticket_data['created_by']}",
            f"🏢 **Customer:** {ticket_data['customer_domain']}",
            "",
            "📝 **TICKET DETAILS**",
            "-"*40,
            f"**Summary:** {ticket_data['summary']}",
            "",
            f"**Description:**",
            ticket_data['description'],
            "",
            "⚙️ **SYSTEM POPULATED FIELDS**",
            "-"*40
        ]
        
        # Add category-specific fields
        excluded_fields = {'ticket_id', 'category', 'query', 'summary', 'description', 'customer_domain', 'created_date', 'created_by'}
        
        for field, value in ticket_data.items():
            if field not in excluded_fields:
                field_display = field.replace('_', ' ').title()
                doc_lines.append(f"**{field_display}:** {value}")
        
        doc_lines.extend([
            "",
            "💼 **CATEGORY-SPECIFIC INFORMATION**",
            "-"*40
        ])
        
        # Add category-specific guidance
        if category == 'NOC':
            doc_lines.extend([
                "**Work Type Options:**",
                "• Task: For scheduling requests or requesting logs",
                "• Outage: For emergency requests (crashed/unresponsive services)",
                "• Access: For access requests"
            ])
        elif category == 'COPS':
            doc_lines.extend([
                "**Typical COPS Activities:**",
                "• Deployment and Provisioning",
                "• Database Operations (Refresh, Changes, Parameters)",
                "• File/Report Requests",
                "• Troubleshooting Support"
            ])
        elif category == 'CSP':
            doc_lines.extend([
                "**CSP Focus Areas:**",
                "• Grant Access Requests",
                "• Revoke Access Requests",
                "• Access Management"
            ])
        elif category in ['MNHT', 'MNLS']:
            doc_lines.extend([
                "**Product Support Request:**",
                "• Technical assistance with Model N products",
                "• Version-specific issue resolution",
                "• Environment-related support"
            ])
        
        doc_lines.extend([
            "",
            "🚨 **IMPORTANT NOTE**",
            "-"*40,
            "This is a SIMULATED ticket created for demonstration purposes.",
            "In production, this would be created in the actual ticketing system",
            "with proper integration and workflow automation.",
            "",
            "="*60
        ])
        
        return "\n".join(doc_lines)
    
    def _save_ticket_to_file(self, ticket_document: str, category: str, customer_domain: str) -> str:
        """Save ticket document to file and return filename"""
        import os
        from datetime import datetime
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), 'ticket_simulation_output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ticket_demo_{category}_{customer_domain.upper()}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ticket_document)
        
        return filename