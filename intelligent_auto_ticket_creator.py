"""
Intelligent Automatic Ticket Creator
Automatically extracts ticket information from user queries with minimal user interaction
"""

import json
import boto3
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from ticket_creator import TicketCreator

class IntelligentAutoTicketCreator(TicketCreator):
    """
    Enhanced ticket creator that automatically extracts information from queries
    and creates tickets with minimal user interaction
    """
    
    def __init__(self):
        super().__init__()
        # Initialize AWS Bedrock client for AI analysis
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        
    def analyze_query_with_ai_response(self, original_query: str, ai_response: str, customer_email: str) -> Dict:
        """
        Use AI to analyze both the user query and AI response to create intelligent ticket questions
        """
        try:
            # Get customer info for context
            customer_domain = customer_email.split('@')[-1] if customer_email else 'unknown.com'
            customer_mapping = self.customer_role_manager.get_customer_mapping(customer_domain)
            
            # Check if this is a support domain (should create Zendesk tickets)
            is_support_domain = self.customer_role_manager.is_support_domain(customer_email)
            print(f"🔍 DEBUG: customer_email={customer_email}, domain={customer_domain}, is_support_domain={is_support_domain}")
            print(f"🔍 DEBUG: support_domains={self.customer_role_manager.get_support_domains()}")
            
            if is_support_domain:
                # Support domains should create Zendesk tickets, not NOC tickets
                print(f"🎫 Support domain detected - will create Zendesk ticket instead of NOC")
                return self._create_zendesk_ticket_smart(original_query, customer_email, ai_response)
            
            # Force database password requests to be NOC for non-support domains only
            is_database_request = 'password' in original_query.lower() and any(keyword in original_query.lower() for keyword in ['database', 'db', 'rodb', 'reset'])
            
            if is_database_request:
                force_category = "NOC"
                category_instruction = "IMPORTANT: This is a database password reset request and MUST be categorized as NOC."
                category_rule = "1. TICKET CATEGORY: MUST BE 'NOC' for database password resets, access issues, and infrastructure problems."
            else:
                force_category = None
                category_instruction = "IMPORTANT: Analyze the request type to determine the appropriate category."
                category_rule = "1. TICKET CATEGORY: Choose the most appropriate category based on the request type:\n   - NOC: Database/infrastructure issues, password resets, system access\n   - COPS: Customer onboarding, setup, configuration\n   - CSP: Data sync, integration, platform issues\n   - MNHT: Documentation, training, how-to questions\n   - MNLS: License, subscription, billing issues"
                
            analysis_prompt = f"""
You are an expert support ticket creator. Analyze the user's original query and the AI response to create intelligent questions for ticket creation.

ORIGINAL USER QUERY: "{original_query}"

AI RESPONSE PROVIDED TO USER:
{ai_response}

CUSTOMER EMAIL: {customer_email}
CUSTOMER ORGANIZATION: {customer_mapping.get('organization', 'Unknown')}

{category_instruction}

CRITICAL INSTRUCTION: Carefully search the AI response for specific details relevant to the request type.

Based on the query and AI response, determine:

{category_rule}

2. SMART_QUESTIONS: Extract specific details from BOTH the AI response and user query. Search thoroughly for:
   - Database hostnames (patterns: *.cloud.modeln.com, *-rdb.*, *-rodb.*, etc.)
   - Service names (SEGPRD, RODB, database names)
   - Port numbers (usually 4 digits)
   - Environment names (Production, RODB Production, etc.)

3. PRIORITY: Based on urgency indicators:
   - Critical: System down, cannot work, production outage
   - High: Blocking work, urgent deadline  
   - Medium: Important but not blocking
   - Low: Enhancement, non-urgent

4. DESCRIPTION: A professional description for the ticket

Respond in JSON format with EXACT extracted values:
{{
    "category": "{force_category if force_category else '[DYNAMIC_CATEGORY]'}",
    "priority": "[High|Medium|Low]", 
    "description": "[Professional description based on request type]",
    "smart_questions": [
        {{
            "field": "database_hostname",
            "question": "Database Hostname:",
            "suggested_value": "EXACT hostname from AI response or empty if not found",
            "required": true,
            "type": "text"
        }},
        {{
            "field": "service_name", 
            "question": "Service Name:",
            "suggested_value": "EXACT service name from AI response or empty if not found",
            "required": true,
            "type": "text"
        }},
        {{
            "field": "environment",
            "question": "Environment:",
            "suggested_value": "EXACT environment from AI response or 'Production' if not specified",
            "required": true,
            "type": "text"
        }},
        {{
            "field": "port_number",
            "question": "Port Number:",
            "suggested_value": "EXACT port from AI response or empty if not found", 
            "required": false,
            "type": "number"
        }}
    ],
    "reasoning": "brief explanation of what was extracted from the AI response"
}}
"""

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": analysis_prompt}]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            if 'content' in response_body and len(response_body['content']) > 0:
                analysis_text = response_body['content'][0]['text']
                # Extract JSON from the response
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis_json = json.loads(analysis_text[json_start:json_end])
                    return analysis_json
            
            return None
            
        except Exception as e:
            print(f"❌ Error analyzing query and AI response: {e}")
            return None

    def analyze_query_for_ticket_info(self, query: str, customer_email: str) -> Dict:
        """
        Use AI to analyze the user query and extract ticket information
        """
        try:
            # Get customer info for context
            customer_domain = customer_email.split('@')[-1] if customer_email else 'unknown.com'
            customer_mapping = self.customer_role_manager.get_customer_mapping(customer_domain)
            
            analysis_prompt = f"""
You are an expert support ticket analyzer. Analyze the following user query and extract relevant ticket information.

USER QUERY: "{query}"
CUSTOMER EMAIL: {customer_email}
CUSTOMER ORGANIZATION: {customer_mapping.get('organization', 'Unknown')}

Based on the query, extract the following information:

1. TICKET CATEGORY: Determine if this is:
   - NOC: Network/infrastructure issues, outages, access problems, monitoring, database passwords
   - COPS: Deployment, provisioning, cloud operations, environment setup
   - CSP: Access requests, Jira permissions, account management
   - MNHT: General Model N Hi-Tech issues (AMD, WDC, Abbott customers)
   - MNLS: General Model N Life Sciences issues (Novartis, Abbvie, Amgen customers)

2. PRIORITY: Based on urgency indicators in the query:
   - Critical: System down, cannot work, production outage
   - High: Blocking work, urgent deadline
   - Medium: Important but not blocking
   - Low: Enhancement, non-urgent

3. AFFECTED AREA: What system/component is affected (if mentioned)

4. ENVIRONMENT: Production, staging, development, etc. (if mentioned)

5. DESCRIPTION: A clear, professional description based on the user's query

6. COMPLETENESS SCORE: Rate from 0-1 how complete the information is:
   - 1.0: All necessary info available, can create ticket immediately
   - 0.7-0.9: Most info available, maybe ask 1-2 clarifying questions
   - 0.5-0.6: Some info missing, need to ask specific questions
   - 0.3-0.4: Minimal info, need several questions
   - 0.0-0.2: Very vague, need extensive clarification

7. MISSING_INFO: List any critical information that's missing and needs to be asked

8. SUGGESTED_QUESTIONS: If completeness < 1.0, suggest 1-3 specific questions to ask

Respond in JSON format:
{{
    "category": "NOC|COPS|CSP|MNHT|MNLS",
    "priority": "Critical|High|Medium|Low",
    "affected_area": "extracted or null",
    "environment": "extracted or null",
    "description": "professional description",
    "completeness_score": 0.0-1.0,
    "missing_info": ["list", "of", "missing", "items"],
    "suggested_questions": ["question1", "question2"],
    "reasoning": "brief explanation of analysis"
}}
"""

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": analysis_prompt}]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            if 'content' in response_body and len(response_body['content']) > 0:
                analysis_text = response_body['content'][0]['text']
                # Extract JSON from the response
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis_json = json.loads(analysis_text[json_start:json_end])
                    return analysis_json
            
            return None
            
        except Exception as e:
            print(f"❌ Error analyzing query with AI: {e}")
            return None
    
    def create_automatic_ticket(self, query: str, customer_email: str, force_create: bool = False) -> Dict:
        """
        Automatically create a ticket with minimal user interaction
        
        Args:
            query: User's original query
            customer_email: Customer email for context
            force_create: If True, create ticket even with incomplete info
            
        Returns:
            Dictionary with ticket info and next steps
        """
        print(f"\n🤖 INTELLIGENT AUTOMATIC TICKET CREATION")
        print("=" * 60)
        
        # Step 1: AI Analysis
        print("🧠 Analyzing query with AI...")
        analysis = self.analyze_query_for_ticket_info(query, customer_email)
        
        if not analysis:
            print("⚠️ AI analysis failed, falling back to standard ticket creation")
            return self.create_ticket(query, customer_email)
        
        print(f"✅ AI Analysis Complete:")
        print(f"   Category: {analysis.get('category', 'Unknown')}")
        print(f"   Priority: {analysis.get('priority', 'Medium')}")
        print(f"   Completeness: {analysis.get('completeness_score', 0.0):.1%}")
        print(f"   Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")
        
        # Step 2: Decision Logic
        completeness = analysis.get('completeness_score', 0.0)
        
        if completeness >= 0.8 or force_create:
            # Sufficient information - create ticket automatically
            print(f"🚀 Sufficient information available ({completeness:.1%}) - Creating ticket automatically...")
            return self._create_ticket_automatically(query, customer_email, analysis)
        
        elif completeness >= 0.5:
            # Some information missing - ask targeted questions
            print(f"❓ Some information missing ({completeness:.1%}) - Will ask specific questions...")
            return self._create_ticket_with_questions(query, customer_email, analysis)
        
        else:
            # Too much information missing - use standard flow
            print(f"⚠️ Insufficient information ({completeness:.1%}) - Using standard ticket flow...")
            return {
                'status': 'needs_form',
                'message': f"I need more information to create your ticket. {analysis.get('reasoning', '')}",
                'suggested_category': analysis.get('category'),
                'analysis': analysis
            }

    def create_smart_ticket_with_context(self, original_query: str, ai_response: str, customer_email: str) -> Dict:
        """
        Create a ticket with smart conversational questions based on AI response context
        
        Args:
            original_query: User's original query
            ai_response: AI response that contains relevant information
            customer_email: Customer email for context
            
        Returns:
            Dictionary with conversational question for ticket creation
        """
        print(f"\n🧠 SMART CONVERSATIONAL TICKET CREATION")
        print("=" * 60)
        
        # Analyze both query and AI response
        print("🔍 Analyzing query and AI response for smart questions...")
        analysis = self.analyze_query_with_ai_response(original_query, ai_response, customer_email)
        
        if not analysis:
            print("⚠️ AI analysis failed, using standard ticket creation")
            return self.create_automatic_ticket(original_query, customer_email)
        
        # Check if a ticket was already created (e.g., Zendesk ticket for support domains)
        if analysis.get('status') == 'created' and analysis.get('ticket_data'):
            print("✅ Ticket already created during analysis (Zendesk), returning result")
            return analysis
        
        print(f"✅ Smart Analysis Complete:")
        print(f"   Category: {analysis.get('category', 'Unknown')}")
        print(f"   Priority: {analysis.get('priority', 'Medium')}")
        print(f"   Smart Questions: {len(analysis.get('smart_questions', []))}")
        print(f"🔍 Full analysis result: {json.dumps(analysis, indent=2)}")
        
        # Get the first question to ask conversationally
        smart_questions = analysis.get('smart_questions', [])
        if smart_questions:
            first_question = smart_questions[0]
            suggested_value = first_question.get('suggested_value', '')
            
            print(f"❓ First question: {first_question.get('question', 'Unknown')}")
            print(f"💡 Suggested value: '{suggested_value}'")
            
            # Create conversational question message
            question_text = f"I'll help you create a {analysis.get('category', 'support')} ticket for your database password reset request.\n\n"
            
            if suggested_value:
                question_text += f"**{first_question['question']}**\nBased on our conversation, I believe this should be: `{suggested_value}`\n\nIs this correct, or would you like to specify a different value?"
            else:
                question_text += f"**{first_question['question']}**\nPlease provide this information to proceed with your ticket creation."
            
            # Store the ticket creation context for next response
            return {
                'status': 'asking_question',
                'category': analysis.get('category'),
                'priority': analysis.get('priority'),
                'description': analysis.get('description'),
                'current_question': first_question,
                'remaining_questions': smart_questions[1:],
                'collected_answers': {},
                'original_query': original_query,
                'customer_email': customer_email,
                'message': question_text,
                'response': question_text
            }
        
        # No questions needed, create ticket directly
        return self._create_ticket_automatically(original_query, customer_email, analysis)

    def continue_smart_ticket_conversation(self, user_answer: str, ticket_context: Dict) -> Dict:
        """
        Continue the conversational ticket creation by processing user's answer
        and asking the next question or creating the ticket
        """
        print(f"\n💬 CONTINUING SMART TICKET CONVERSATION")
        print(f"👤 User answer: '{user_answer}'")
        print(f"📋 Ticket context keys: {list(ticket_context.keys())}")
        print("=" * 50)
        
        current_question = ticket_context.get('current_question', {})
        remaining_questions = ticket_context.get('remaining_questions', [])
        collected_answers = ticket_context.get('collected_answers', {})
        
        print(f"❓ Current question field: {current_question.get('field')}")
        print(f"📊 Remaining questions: {len(remaining_questions)}")
        print(f"💾 Collected answers so far: {list(collected_answers.keys())}")
        
        # Process the current answer
        field_name = current_question.get('field')
        if field_name:
            # Check if user confirmed the suggested value or provided a new one
            suggested_value = current_question.get('suggested_value', '')
            user_answer_lower = user_answer.lower().strip()
            
            print(f"🔍 Suggested value: '{suggested_value}'")
            print(f"🔍 User answer: '{user_answer_lower}'")
            
            if user_answer_lower in ['yes', 'correct', 'that\'s right', 'confirmed', 'ok', 'okay', 'y']:
                # User confirmed the suggested value
                collected_answers[field_name] = suggested_value
                print(f"✅ User confirmed: {field_name} = {suggested_value}")
            else:
                # User provided a different value
                collected_answers[field_name] = user_answer.strip()
                print(f"✅ User provided: {field_name} = {user_answer.strip()}")
        else:
            print("⚠️ No current question field found!")
        
        # Check if there are more questions
        if remaining_questions:
            print(f"➡️ Moving to next question ({len(remaining_questions)} remaining)")
            next_question = remaining_questions[0]
            remaining_after_next = remaining_questions[1:]
            suggested_value = next_question.get('suggested_value', '')
            
            print(f"❓ Next question: {next_question.get('question')}")
            print(f"💡 Next suggested value: '{suggested_value}'")
            
            # Create next conversational question
            if suggested_value:
                question_text = f"**{next_question['question']}**\nBased on our conversation, I believe this should be: `{suggested_value}`\n\nIs this correct, or would you like to specify a different value?"
            else:
                question_text = f"**{next_question['question']}**\nPlease provide this information to continue with your ticket creation."
            
            # Update context for next iteration
            updated_context = ticket_context.copy()
            updated_context['current_question'] = next_question
            updated_context['remaining_questions'] = remaining_after_next
            updated_context['collected_answers'] = collected_answers
            
            print(f"🔄 Returning next question, context updated")
            return {
                'status': 'asking_question',
                'message': question_text,
                'response': question_text,
                'ticket_context': updated_context
            }
        
        # All questions answered, create the ticket
        print(f"🎫 All questions answered! Creating ticket with collected data:")
        for field, value in collected_answers.items():
            print(f"   ✅ {field}: {value}")
        
        # Create ticket with collected information
        result = self._create_ticket_with_collected_answers(
            ticket_context.get('original_query'),
            ticket_context.get('customer_email'),
            ticket_context.get('category'),
            ticket_context.get('priority'),
            ticket_context.get('description'),
            collected_answers
        )
        
        print(f"🎫 Ticket creation result: {result.get('status')}")
        return result

    def _create_ticket_with_collected_answers(self, original_query: str, customer_email: str, 
                                           category: str, priority: str, description: str, 
                                           collected_answers: Dict) -> Dict:
        """
        Create the final ticket with all collected information
        """
        try:
            # Extract customer info
            customer_domain = customer_email.split('@')[-1] if customer_email else 'unknown.com'
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie',
                'amgen.com': 'Amgen'
            }
            customer = domain_to_customer.get(customer_domain, customer_domain.split('.')[0].capitalize())
            
            # Generate ticket data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ticket_id = f"TICKET_{category}_{customer}_{timestamp}"
            
            # Generate JIRA ticket ID
            import random
            random_number = random.randint(10000, 99999)
            jira_ticket_id = f"{category}-{random_number}"
            
            # Build detailed description with technical details
            detailed_description = description
            if collected_answers:
                technical_details = []
                for field, value in collected_answers.items():
                    field_label = field.replace('_', ' ').title()
                    technical_details.append(f"• {field_label}: {value}")
                
                if technical_details:
                    detailed_description += f"\n\n**Technical Details:**\n" + "\n".join(technical_details)
            
            ticket_data = {
                'ticket_id': ticket_id,
                'jira_ticket_id': jira_ticket_id,
                'category': category,
                'customer': customer,
                'customer_email': customer_email,
                'original_query': original_query,
                'created_date': datetime.now().isoformat(),
                'priority': priority,
                'description': detailed_description
            }
            
            # Save ticket to file
            self.save_ticket_to_file(ticket_data)
            
            print(f"✅ Smart conversational ticket created successfully!")
            print(f"   Ticket ID: {ticket_id}")
            print(f"   Category: {category}")
            print(f"   Priority: {priority}")
            
            return {
                'status': 'created',
                'ticket_id': ticket_id,
                'ticket_data': ticket_data,
                'message': f"✅ **Ticket Created Successfully!**\n\n🎫 **Ticket ID:** {ticket_id}\n📧 **Category:** {category}\n⚡ **Priority:** {priority}\n\nYour database password reset request has been submitted with all the necessary details. Our support team will process your request and provide you with new credentials.\n\nYou should receive an update shortly via email. Is there anything else I can help you with?",
                'response': f"✅ **Ticket Created Successfully!**\n\n🎫 **Ticket ID:** {ticket_id}\n📧 **Category:** {category}\n⚡ **Priority:** {priority}\n\nYour database password reset request has been submitted with all the necessary details. Our support team will process your request and provide you with new credentials.\n\nYou should receive an update shortly via email. Is there anything else I can help you with?"
            }
            
        except Exception as e:
            print(f"❌ Error creating smart conversational ticket: {e}")
            return {
                'status': 'error',
                'message': f'Error creating ticket: {str(e)}'
            }
    
    def _create_ticket_automatically(self, query: str, customer_email: str, analysis: Dict) -> Dict:
        """
        Create ticket immediately using AI-extracted information
        """
        try:
            # Extract customer info
            customer_domain = customer_email.split('@')[-1] if customer_email else 'unknown.com'
            domain_to_customer = {
                'amd.com': 'AMD',
                'novartis.com': 'Novartis',
                'wdc.com': 'Wdc',
                'abbott.com': 'Abbott',
                'abbvie.com': 'Abbvie',
                'amgen.com': 'Amgen'
            }
            customer = domain_to_customer.get(customer_domain, customer_domain.split('.')[0].capitalize())
            
            # Use AI-determined category or fallback to domain mapping
            category = analysis.get('category')
            if not category:
                category = self.determine_ticket_category(query, customer, customer_email)
            
            # Generate ticket data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ticket_id = f"TICKET_{category}_{customer}_{timestamp}"
            
            ticket_data = {
                'ticket_id': ticket_id,
                'category': category,
                'customer': customer,
                'customer_email': customer_email,
                'original_query': query,
                'created_date': datetime.now().isoformat(),
                'creation_method': 'automatic_ai',
                'ai_analysis': analysis,
                'completeness_score': analysis.get('completeness_score', 1.0)
            }
            
            # Add AI-extracted fields
            if analysis.get('description'):
                ticket_data['description'] = analysis['description']
            else:
                ticket_data['description'] = f"User Query: {query}"
            
            if analysis.get('priority'):
                ticket_data['priority'] = analysis['priority']
                
            if analysis.get('affected_area'):
                ticket_data['area'] = analysis['affected_area']
                
            if analysis.get('environment'):
                ticket_data['environment'] = analysis['environment']
            
            # Add auto-populated fields based on category
            auto_fields = self.get_populated_fields_for_category(category)
            for field, value in auto_fields.items():
                if field not in ticket_data:
                    # Resolve dynamic values
                    if isinstance(value, str):
                        if 'based on description' in value.lower():
                            ticket_data[field] = f"Support Request: {query[:80]}{'...' if len(query) > 80 else ''}"
                        elif 'based on customer organization' in value.lower():
                            customer_mapping = self.customer_role_manager.get_customer_mapping(customer_domain)
                            ticket_data[field] = customer_mapping.get('organization', customer)
                        elif 'current_date' in value.lower():
                            ticket_data[field] = datetime.now().strftime('%Y-%m-%d')
                        else:
                            ticket_data[field] = value
                    else:
                        ticket_data[field] = value
            
            # Save ticket to file
            self.save_ticket_to_file(ticket_data)
            
            print(f"✅ Automatic ticket created successfully!")
            print(f"   Ticket ID: {ticket_id}")
            print(f"   Category: {category}")
            print(f"   Priority: {ticket_data.get('priority', 'Medium')}")
            
            return {
                'status': 'created',
                'ticket_data': ticket_data,
                'message': f"🎫 **Ticket Created Automatically!**\n\n**Ticket ID:** {ticket_id}\n**Category:** {category}\n**Priority:** {ticket_data.get('priority', 'Medium')}\n\nYour support request has been processed and a ticket has been created with the information from your query. Our support team will review and respond accordingly.",
                'auto_created': True
            }
            
        except Exception as e:
            print(f"❌ Error creating automatic ticket: {e}")
            return {'status': 'error', 'message': f"Error creating ticket: {e}"}
    
    def _create_ticket_with_questions(self, query: str, customer_email: str, analysis: Dict) -> Dict:
        """
        Create ticket after asking only the essential missing questions
        """
        missing_info = analysis.get('missing_info', [])
        suggested_questions = analysis.get('suggested_questions', [])
        
        # Return structure for frontend to ask specific questions
        return {
            'status': 'needs_questions',
            'analysis': analysis,
            'missing_info': missing_info,
            'questions': suggested_questions,
            'message': f"I can create a ticket for you! I just need a bit more information:",
            'partial_ticket_data': {
                'category': analysis.get('category'),
                'priority': analysis.get('priority', 'Medium'),
                'description': analysis.get('description', query),
                'affected_area': analysis.get('affected_area'),
                'environment': analysis.get('environment')
            }
        }
    
    def complete_ticket_with_answers(self, query: str, customer_email: str, analysis: Dict, answers: Dict) -> Dict:
        """
        Complete ticket creation after getting answers to specific questions
        """
        # Merge AI analysis with user answers
        enhanced_analysis = analysis.copy()
        enhanced_analysis.update(answers)
        enhanced_analysis['completeness_score'] = 1.0  # Now complete
        
        # Create the ticket with complete information
        return self._create_ticket_automatically(query, customer_email, enhanced_analysis)
    
    def create_minimal_communication_ticket(self, query: str, customer_email: str) -> Dict:
        """
        Create a ticket with absolutely minimal user communication - extract everything possible from query
        """
        print(f"\n🎯 MINIMAL COMMUNICATION TICKET CREATION")
        print("=" * 60)
        
        # Force create ticket with whatever info we can extract
        analysis = self.analyze_query_for_ticket_info(query, customer_email)
        
        if analysis:
            # Enhance the analysis to fill in gaps with smart defaults
            if not analysis.get('priority'):
                analysis['priority'] = 'Medium'  # Default priority
            
            if not analysis.get('affected_area'):
                # Try to guess from query keywords
                query_lower = query.lower()
                if any(word in query_lower for word in ['login', 'access', 'password', 'authentication']):
                    analysis['affected_area'] = 'Access'
                elif any(word in query_lower for word in ['database', 'db', 'sql']):
                    analysis['affected_area'] = 'Database'
                elif any(word in query_lower for word in ['network', 'connection', 'connectivity']):
                    analysis['affected_area'] = 'Network'
                elif any(word in query_lower for word in ['application', 'app', 'software']):
                    analysis['affected_area'] = 'Application'
                else:
                    analysis['affected_area'] = 'General'
            
            if not analysis.get('environment'):
                # Use proper environment detection - only auto-fill if explicitly mentioned
                from environment_detection import detect_environment_from_query
                detected_env, confidence = detect_environment_from_query(query)
                if detected_env:
                    analysis['environment'] = detected_env
                else:
                    # Don't default to production - leave as None to prompt user
                    analysis['environment'] = None
            
            analysis['completeness_score'] = 1.0  # Force complete
            
            result = self._create_ticket_automatically(query, customer_email, analysis)
            if result.get('status') == 'created':
                result['ticket_data']['creation_method'] = 'minimal_communication_ai'
                result['ticket_data']['ai_extraction_used'] = True
                
                # Save the enhanced ticket
                self.save_ticket_to_file(result['ticket_data'])
                
                # Update the message to reflect minimal communication approach
                ticket_id = result['ticket_data']['ticket_id']
                category = result['ticket_data']['category']
                priority = result['ticket_data'].get('priority', 'Medium')
                
                result['message'] = f"""🎫 **Ticket Created Successfully!**

**Ticket ID:** {ticket_id}
**Category:** {category}  
**Priority:** {priority}

Your ticket has been created automatically using AI-powered analysis of your query. All available information has been extracted and the ticket includes:

✅ **Automatically Detected:**
• Category: {category}
• Priority: {priority}  
• Area: {analysis.get('affected_area', 'General')}
• Environment: {analysis.get('environment', 'production')}

Our support team will review your request and respond accordingly. You can download the ticket details below."""
                
                return result
        
        # Fallback if AI analysis fails
        return self.create_ticket(query, customer_email)

    def save_ticket_to_file(self, ticket_data: Dict) -> str:
        """Save ticket to file with enhanced format"""
        output_dir = 'ticket_simulation_output'
        os.makedirs(output_dir, exist_ok=True)
        
        ticket_id = ticket_data.get('ticket_id', 'UNKNOWN')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use ticket type indicator instead of creation_method
        filename = f"ticket_automatic_ai_{ticket_id.replace('TICKET_', '')}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Format ticket content
        content = self._format_enhanced_ticket_content(ticket_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Ticket saved to: {filepath}")
        return filepath
    
    def _format_enhanced_ticket_content(self, ticket_data: Dict) -> str:
        """Format ticket content with AI analysis information"""
        
        header = "AUTOMATIC AI TICKET"
        
        content = f"""{header}
{'=' * len(header)}

Ticket ID: {ticket_data.get('ticket_id', 'N/A')}
Jira Ticket ID: {ticket_data.get('jira_ticket_id', 'N/A')}
Category: {ticket_data.get('category', 'N/A')}
Customer: {ticket_data.get('customer', 'N/A')}
Priority: {ticket_data.get('priority', 'Medium')}
Description: {ticket_data.get('description', 'N/A')}

This ticket was created automatically using AI analysis.

TICKET STATUS: CREATED
NEXT STEPS: Support team will review and respond
"""

        return content
    
    def _create_zendesk_ticket_smart(self, original_query: str, customer_email: str, ai_response: str) -> Dict:
        """
        Create a Zendesk ticket for support domains instead of NOC ticket
        """
        try:
            print(f"🎫 Creating Zendesk ticket for support domain: {customer_email}")
            
            # Use the enhanced Zendesk ticket creation from fastapi_server
            from fastapi_server import create_zendesk_ticket_intelligent
            
            # Get conversation context if available
            conversation_context = []
            try:
                from chat_history_manager import ChatHistoryManager
                chat_manager = ChatHistoryManager()
                conversation_context = chat_manager.get_history(customer_email) or []
            except Exception as e:
                print(f"⚠️ Could not get conversation context: {e}")
            
            # Create Zendesk ticket with AI analysis
            zendesk_result = create_zendesk_ticket_intelligent(
                original_query, 
                customer_email, 
                ai_response=ai_response, 
                conversation_context=conversation_context
            )
            print(f"🔍 DEBUG: Zendesk result = {zendesk_result}")
            
            if zendesk_result.get('status') == 'created':
                return {
                    'status': 'created',
                    'ticket_data': zendesk_result.get('ticket_data', {}),
                    'message': f"✅ Zendesk support ticket created successfully!\n\n**Ticket ID:** {zendesk_result.get('ticket_data', {}).get('ticket_id', 'N/A')}\n\nYour support request has been submitted to our Zendesk system and our team will review it shortly. You should receive updates via email.\n\nIs there anything else I can help you with today?"
                }
            else:
                return {
                    'status': 'error',
                    'message': f"Failed to create Zendesk ticket: {zendesk_result.get('message', 'Unknown error')}"
                }
                
        except Exception as e:
            print(f"❌ Error creating Zendesk ticket: {e}")
            return {
                'status': 'error',
                'message': f"Failed to create Zendesk ticket: {str(e)}"
            }