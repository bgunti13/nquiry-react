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
                # Default to production if not specified
                query_lower = query.lower()
                if 'test' in query_lower or 'staging' in query_lower:
                    analysis['environment'] = 'staging'
                elif 'dev' in query_lower or 'development' in query_lower:
                    analysis['environment'] = 'development'
                else:
                    analysis['environment'] = 'production'
            
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
        filename = f"ticket_{ticket_data.get('creation_method', 'standard')}_{ticket_id.replace('TICKET_', '')}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Format ticket content
        content = self._format_enhanced_ticket_content(ticket_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Ticket saved to: {filepath}")
        return filepath
    
    def _format_enhanced_ticket_content(self, ticket_data: Dict) -> str:
        """Format ticket content with AI analysis information"""
        creation_method = ticket_data.get('creation_method', 'standard')
        ai_analysis = ticket_data.get('ai_analysis', {})
        
        if creation_method == 'minimal_communication_ai':
            header = "MINIMAL COMMUNICATION TICKET"
            subheader = "Created using AI-powered field extraction"
        elif creation_method == 'automatic_ai':
            header = "INTELLIGENT AUTOMATIC TICKET"
            subheader = "Created using AI analysis with high confidence"
        else:
            header = "SUPPORT TICKET"
            subheader = "Standard ticket creation"
        
        content = f"""{header}
{'=' * len(header)}

{subheader}
Creation Method: {creation_method.replace('_', ' ').title()}
AI Completeness Score: {ticket_data.get('completeness_score', 0.0):.1%}

Ticket Id: {ticket_data.get('ticket_id', 'N/A')}
Category: {ticket_data.get('category', 'N/A')}
Customer: {ticket_data.get('customer', 'N/A')}
Customer Email: {ticket_data.get('customer_email', 'N/A')}
Original Query: {ticket_data.get('original_query', 'N/A')}
Created Date: {ticket_data.get('created_date', 'N/A')}"""

        if creation_method in ['automatic_ai', 'minimal_communication_ai']:
            content += f"""
Creation Method: {creation_method}
Ai Extraction Used: {ticket_data.get('ai_extraction_used', True)}
Completeness Score: {ticket_data.get('completeness_score', 0.0)}"""

        # Add ticket fields
        content += f"""
Priority: {ticket_data.get('priority', 'Medium')}
Area Affected: {ticket_data.get('area', ticket_data.get('affected_area', 'N/A'))}
Environment: {ticket_data.get('environment', 'N/A')}
Description: {ticket_data.get('description', 'N/A')}"""

        # Add auto-populated fields
        auto_fields = ['project', 'work_type', 'summary', 'cloud_operations_request_type', 'support_org']
        for field in auto_fields:
            if field in ticket_data:
                field_name = field.replace('_', ' ').title()
                content += f"\n{field_name}: {ticket_data[field]}"

        if ai_analysis and creation_method in ['automatic_ai', 'minimal_communication_ai']:
            content += f"""

AI ANALYSIS DETAILS:
===================
Reasoning: {ai_analysis.get('reasoning', 'N/A')}
Detected Category: {ai_analysis.get('category', 'N/A')}
Confidence Level: {ticket_data.get('completeness_score', 0.0):.1%}"""

            if ai_analysis.get('missing_info'):
                content += f"\nMissing Information: {', '.join(ai_analysis['missing_info'])}"

        content += f"""

TICKET STATUS: CREATED
NEXT STEPS: Support team will review and respond
"""

        return content