"""
Rule-Based Intelligent Ticket Creator
Creates tickets intelligently without requiring AI/Bedrock when credentials are not available
Uses pattern matching and rules to extract ticket information from user queries
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from ticket_creator import TicketCreator

class RuleBasedTicketCreator(TicketCreator):
    """
    Enhanced ticket creator that uses rule-based analysis to extract information from queries
    and creates tickets with minimal user interaction - no AI required
    """
    
    def __init__(self):
        super().__init__()
        
        # Priority keywords for automatic detection
        self.priority_keywords = {
            'critical': ['down', 'outage', 'crashed', 'not working', 'system failure', 'urgent', 'critical', 'production down', 'emergency'],
            'high': ['blocking', 'urgent', 'deadline', 'asap', 'high priority', 'important', 'stuck', 'cannot proceed'],
            'medium': ['issue', 'problem', 'error', 'trouble', 'difficulty', 'bug', 'help'],
            'low': ['question', 'enhancement', 'request', 'suggestion', 'improvement', 'how to', 'can you']
        }
        
        # Area keywords for automatic detection
        self.area_keywords = {
            'Access': ['login', 'access', 'password', 'authentication', 'sign in', 'log in', 'permissions', 'authorization'],
            'Database': ['database', 'db', 'sql', 'query', 'data', 'table', 'connection'],
            'Network': ['network', 'connection', 'connectivity', 'timeout', 'slow', 'latency'],
            'Application': ['application', 'app', 'software', 'system', 'interface', 'ui', 'screen'],
            'API': ['api', 'endpoint', 'rest', 'service', 'integration', 'webhook'],
            'Configuration': ['config', 'configuration', 'setting', 'setup', 'parameter'],
            'Performance': ['slow', 'performance', 'speed', 'lag', 'timeout', 'hanging'],
            'Deployment': ['deployment', 'deploy', 'release', 'publish', 'build']
        }
        
        # Environment keywords for automatic detection
        self.environment_keywords = {
            'production': ['production', 'prod', 'live', 'main'],
            'staging': ['staging', 'stage', 'test', 'testing'],
            'development': ['development', 'dev', 'local', 'sandbox']
        }
    
    def analyze_query_rule_based(self, query: str, customer_email: str) -> Dict:
        """
        Use rule-based analysis to extract ticket information from the query
        """
        query_lower = query.lower()
        
        # Get customer info for context
        customer_domain = customer_email.split('@')[-1] if customer_email else 'unknown.com'
        customer_mapping = self.customer_role_manager.get_customer_mapping(customer_domain)
        
        analysis = {
            'category': None,
            'priority': 'Medium',
            'affected_area': None,
            'environment': 'production',  # Default
            'description': query,
            'completeness_score': 0.0,
            'missing_info': [],
            'suggested_questions': [],
            'reasoning': 'Rule-based analysis'
        }
        
        # 1. Determine category using existing logic
        customer = customer_mapping.get('organization', 'Unknown')
        category = self.determine_ticket_category(query, customer, customer_email)
        analysis['category'] = category
        
        # 2. Determine priority based on keywords
        priority_score = 0
        detected_priority = 'Medium'
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if priority == 'critical':
                        priority_score = max(priority_score, 4)
                        detected_priority = 'Critical'
                    elif priority == 'high':
                        priority_score = max(priority_score, 3)
                        detected_priority = 'High'
                    elif priority == 'medium':
                        priority_score = max(priority_score, 2)
                        detected_priority = 'Medium'
                    elif priority == 'low':
                        priority_score = max(priority_score, 1)
                        detected_priority = 'Low'
        
        analysis['priority'] = detected_priority
        
        # 3. Determine affected area
        for area, keywords in self.area_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    analysis['affected_area'] = area
                    break
            if analysis['affected_area']:
                break
        
        if not analysis['affected_area']:
            analysis['affected_area'] = 'General'
        
        # 4. Determine environment
        for env, keywords in self.environment_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    analysis['environment'] = env
                    break
            if analysis['environment'] != 'production':
                break
        
        # 5. Calculate completeness score
        score = 0.4  # Base score for having a query
        
        if analysis['category']:
            score += 0.2
        if analysis['priority']:
            score += 0.1
        if analysis['affected_area'] and analysis['affected_area'] != 'General':
            score += 0.2
        if analysis['environment']:
            score += 0.1
        
        # Bonus for longer, more detailed queries
        if len(query) > 50:
            score += 0.1
        if len(query) > 100:
            score += 0.1
        
        analysis['completeness_score'] = min(score, 1.0)
        
        # 6. Determine missing info and questions
        required_fields = self.get_required_fields_for_category(category)
        
        # For NOC and COPS, description is usually enough
        if category in ['NOC', 'COPS']:
            if analysis['completeness_score'] >= 0.7:
                analysis['completeness_score'] = 1.0  # Good enough for these categories
            else:
                analysis['missing_info'] = ['more specific description']
                analysis['suggested_questions'] = ['Can you provide more details about the specific issue you\'re experiencing?']
        
        # For MNHT and MNLS, we might need more info
        elif category in ['MNHT', 'MNLS']:
            missing = []
            questions = []
            
            if 'area' in required_fields and not analysis.get('affected_area'):
                missing.append('affected area')
                questions.append('Which area or component is affected by this issue?')
            
            if 'affected_version' in required_fields:
                # Check if version is mentioned in query
                version_pattern = r'\b(?:v|version|ver)\.?\s*[\d\.]+\b'
                if not re.search(version_pattern, query_lower, re.IGNORECASE):
                    missing.append('version information')
                    questions.append('Which version of the system are you experiencing this issue with?')
            
            analysis['missing_info'] = missing
            analysis['suggested_questions'] = questions
            
            # Adjust completeness score
            if len(missing) == 0:
                analysis['completeness_score'] = min(analysis['completeness_score'] + 0.2, 1.0)
            elif len(missing) <= 2:
                analysis['completeness_score'] = max(analysis['completeness_score'], 0.6)
        
        analysis['reasoning'] = f"Rule-based analysis detected {category} category with {detected_priority} priority for {analysis['affected_area']} area"
        
        return analysis
    
    def create_automatic_ticket_rule_based(self, query: str, customer_email: str, force_create: bool = False) -> Dict:
        """
        Create a ticket automatically using rule-based analysis (no AI required)
        """
        print(f"\n🤖 RULE-BASED INTELLIGENT TICKET CREATION")
        print("=" * 60)
        
        # Step 1: Rule-based Analysis
        print("🧠 Analyzing query with rule-based logic...")
        analysis = self.analyze_query_rule_based(query, customer_email)
        
        print(f"✅ Rule-based Analysis Complete:")
        print(f"   Category: {analysis.get('category', 'Unknown')}")
        print(f"   Priority: {analysis.get('priority', 'Medium')}")
        print(f"   Area: {analysis.get('affected_area', 'General')}")
        print(f"   Environment: {analysis.get('environment', 'production')}")
        print(f"   Completeness: {analysis.get('completeness_score', 0.0):.1%}")
        print(f"   Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")
        
        # Step 2: Decision Logic
        completeness = analysis.get('completeness_score', 0.0)
        
        if completeness >= 0.7 or force_create:
            # Sufficient information - create ticket automatically
            print(f"🚀 Sufficient information available ({completeness:.1%}) - Creating ticket automatically...")
            return self._create_ticket_automatically_rule_based(query, customer_email, analysis)
        
        elif completeness >= 0.5:
            # Some information missing - ask targeted questions
            print(f"❓ Some information missing ({completeness:.1%}) - Will ask specific questions...")
            return self._create_ticket_with_questions_rule_based(query, customer_email, analysis)
        
        else:
            # Too much information missing - use standard flow
            print(f"⚠️ Insufficient information ({completeness:.1%}) - Using standard ticket flow...")
            return {
                'status': 'needs_form',
                'message': f"I need more information to create your ticket. {analysis.get('reasoning', '')}",
                'suggested_category': analysis.get('category'),
                'analysis': analysis
            }
    
    def _create_ticket_automatically_rule_based(self, query: str, customer_email: str, analysis: Dict) -> Dict:
        """
        Create ticket immediately using rule-based extracted information
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
            
            # Use analysis results
            category = analysis.get('category', 'MNHT')
            
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
                'creation_method': 'automatic_rule_based',
                'rule_analysis': analysis,
                'completeness_score': analysis.get('completeness_score', 1.0)
            }
            
            # Add rule-based extracted fields
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
                'message': f"🎫 **Ticket Created Automatically!**\n\n**Ticket ID:** {ticket_id}\n**Category:** {category}\n**Priority:** {ticket_data.get('priority', 'Medium')}\n**Area:** {ticket_data.get('area', 'General')}\n**Environment:** {ticket_data.get('environment', 'production')}\n\nYour support request has been processed automatically using intelligent analysis. Our support team will review and respond accordingly.",
                'auto_created': True,
                'method': 'rule_based'
            }
            
        except Exception as e:
            print(f"❌ Error creating automatic ticket: {e}")
            return {'status': 'error', 'message': f"Error creating ticket: {e}"}
    
    def _create_ticket_with_questions_rule_based(self, query: str, customer_email: str, analysis: Dict) -> Dict:
        """
        Create ticket after asking only the essential missing questions (rule-based)
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
    
    def save_ticket_to_file(self, ticket_data: Dict) -> str:
        """Save ticket to file with enhanced format"""
        output_dir = 'ticket_simulation_output'
        os.makedirs(output_dir, exist_ok=True)
        
        ticket_id = ticket_data.get('ticket_id', 'UNKNOWN')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        method = ticket_data.get('creation_method', 'standard')
        filename = f"ticket_{method}_{ticket_id.replace('TICKET_', '')}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Format ticket content
        content = self._format_rule_based_ticket_content(ticket_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Ticket saved to: {filepath}")
        return filepath
    
    def _format_rule_based_ticket_content(self, ticket_data: Dict) -> str:
        """Format ticket content with rule-based analysis information"""
        creation_method = ticket_data.get('creation_method', 'standard')
        rule_analysis = ticket_data.get('rule_analysis', {})
        
        if creation_method == 'automatic_rule_based':
            header = "INTELLIGENT RULE-BASED TICKET"
            subheader = "Created using intelligent rule-based analysis"
        else:
            header = "SUPPORT TICKET"
            subheader = "Standard ticket creation"
        
        content = f"""{header}
{'=' * len(header)}

{subheader}
Analysis Completeness Score: {ticket_data.get('completeness_score', 0.0):.1%}

Ticket Id: {ticket_data.get('ticket_id', 'N/A')}
Category: {ticket_data.get('category', 'N/A')}
Customer: {ticket_data.get('customer', 'N/A')}
Customer Email: {ticket_data.get('customer_email', 'N/A')}
Original Query: {ticket_data.get('original_query', 'N/A')}
Created Date: {ticket_data.get('created_date', 'N/A')}
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

        if rule_analysis and creation_method == 'automatic_rule_based':
            content += f"""

RULE-BASED ANALYSIS DETAILS:
============================
Reasoning: {rule_analysis.get('reasoning', 'N/A')}
Detected Category: {rule_analysis.get('category', 'N/A')}
Detected Priority: {rule_analysis.get('priority', 'N/A')}
Detected Area: {rule_analysis.get('affected_area', 'N/A')}
Detected Environment: {rule_analysis.get('environment', 'N/A')}
Confidence Level: {ticket_data.get('completeness_score', 0.0):.1%}"""

            if rule_analysis.get('missing_info'):
                content += f"\nMissing Information: {', '.join(rule_analysis['missing_info'])}"

        content += f"""

TICKET STATUS: CREATED
NEXT STEPS: Support team will review and respond
"""

        return content