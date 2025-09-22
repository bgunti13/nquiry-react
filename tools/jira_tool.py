"""
JIRA REST API Tool for accessing JIRA instances
"""

import os
import requests
import json
import warnings
from typing import List, Dict, Any, Optional
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Suppress SSL warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Load environment variables
load_dotenv()

class JiraTool:
    """Tool for interacting with JIRA REST API"""
    
    def __init__(self):
        """Initialize JIRA tool with configuration from environment and load customer-org mapping"""
        self.base_url = (os.getenv('JIRA_BASE_URL')
                         or os.getenv('JIRA_URL'))
        self.username = os.getenv('JIRA_USERNAME')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([self.base_url, self.username, self.api_token]):
            print("⚠️  JIRA configuration incomplete. Please set JIRA_BASE_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env")
        
        # Ensure base_url ends with /rest/api/3/
        if self.base_url and not self.base_url.endswith('/'):
            self.base_url += '/'
        if self.base_url and not self.base_url.endswith('rest/api/3/'):
            if not self.base_url.endswith('rest/api/3'):
                self.base_url += 'rest/api/3/'
        
        self.session = requests.Session()
        if self.username and self.api_token:
            self.session.auth = HTTPBasicAuth(self.username, self.api_token)
        
        # Disable SSL verification to avoid handshake issues with corporate certificates
        self.session.verify = False
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Load customer-org mapping from Excel
        self._load_customer_mapping()
    
    def _extract_text_from_adf(self, adf_content):
        """
        Extract plain text from Atlassian Document Format (ADF) content
        
        Args:
            adf_content: ADF content (dict) or plain string
            
        Returns:
            Extracted plain text string
        """
        if not adf_content:
            return ""
        
        # If it's already a string, return as-is
        if isinstance(adf_content, str):
            return adf_content
        
        # If it's not a dict, convert to string
        if not isinstance(adf_content, dict):
            return str(adf_content)
        
        def extract_text_recursive(node):
            """Recursively extract text from ADF nodes"""
            if not isinstance(node, dict):
                return str(node) if node else ""
            
            text_parts = []
            
            # Handle text nodes
            if node.get('type') == 'text':
                return node.get('text', '')
            
            # Handle content arrays
            if 'content' in node and isinstance(node['content'], list):
                for child in node['content']:
                    text_parts.append(extract_text_recursive(child))
            
            # Handle other known node types
            node_type = node.get('type', '')
            if node_type in ['paragraph', 'doc', 'blockquote']:
                # These typically contain content
                pass
            elif node_type == 'hardBreak':
                text_parts.append('\n')
            elif node_type == 'listItem':
                text_parts.append('• ')
            
            return ''.join(text_parts)
        
        try:
            extracted_text = extract_text_recursive(adf_content)
            return extracted_text.strip()
        except Exception as e:
            # Fallback to string conversion
            return str(adf_content)
    
    def _load_customer_mapping(self):
        """Load customer-org mapping from Excel"""
        self.customer_org_map = {}
        try:
            import pandas as pd
            excel_path = os.path.join(os.path.dirname(__file__), '..', 'LS-HT Customer Info.xlsx')
            
            # Read from both HT and LS sheets
            for sheet_name in ['HT', 'LS']:
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    
                    # Build mapping from this sheet
                    for _, row in df.iterrows():
                        customer = str(row.get('Customer', '')).strip().lower().replace(' ', '')
                        # Try different column name variations
                        jira_org = (str(row.get('JIRA Organisation', '')).strip() or 
                                   str(row.get('JIRA Organization', '')).strip() or
                                   str(row.get('JIRA Organization ', '')).strip())
                        if customer and jira_org and jira_org != 'nan':
                            self.customer_org_map[customer] = jira_org
                    
                except Exception as sheet_error:
                    print(f"Could not load {sheet_name} sheet: {sheet_error}")
            
            print(f"✅ Loaded {len(self.customer_org_map)} customer mappings")
            
        except Exception as e:
            print(f"⚠️ Could not load customer-org mapping from Excel: {e}")
    
    def reload_customer_mapping(self):
        """Reload customer-org mapping from Excel (for debugging)"""
        self._load_customer_mapping()

    def test_connection(self) -> bool:
        """Test connection to JIRA API with retry logic"""
        max_retries = 3
        timeout_seconds = 30
        
        for attempt in range(max_retries):
            try:
                if not all([self.base_url, self.username, self.api_token]):
                    return False
                
                response = self.session.get(f"{self.base_url}myself", timeout=timeout_seconds)
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"🔧 JIRA Debug: Connection failed with status {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                    continue
                else:
                    print("🔧 JIRA Debug: All attempts failed due to timeout")
                    
            except Exception as e:
                print(f"JIRA connection test failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                    continue
                else:
                    break
                    
        return False
    
    def _get_organization_variations(self, organization: str) -> List[str]:
        """
        Get all variations of an organization name for comprehensive searching using Excel mapping
        Args:
            organization: The organization name from customer mapping
        Returns:
            List of organization name variations to search for
        """
        # Reload mapping if empty
        if not self.customer_org_map:
            self.reload_customer_mapping()
            
        variations = [organization]
        # Normalize lookup value
        org_key = organization.strip().lower().replace(' ', '')
        
        mapped_jira_org = self.customer_org_map.get(org_key)
        if mapped_jira_org:
            variations.append(mapped_jira_org)
            
        # Add common variations (spaces, cases, etc.)
        base_variations = [
            organization.replace(" ", "-"),
            organization.replace(" ", "_"),
            organization.replace(" ", ""),
            organization.upper(),
            organization.lower()
        ]
        
        if mapped_jira_org:
            base_variations.extend([
                mapped_jira_org.replace(" ", "-"),
                mapped_jira_org.replace(" ", "_"),
                mapped_jira_org.replace(" ", ""),
                mapped_jira_org.upper(),
                mapped_jira_org.lower()
            ])
            
        variations.extend(base_variations)
        # Remove duplicates and return
        result = list(set([v for v in variations if v]))
        return result

    def search_issues_by_organization(self, query: str, organization: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search JIRA issues for a specific organization
        
        Args:
            query: Search query string
            organization: Organization name to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of JIRA issues filtered by organization
        """
        try:
            if not self.test_connection():
                print("❌ JIRA connection not available")
                return []
            
            # Get all organization variations using the mapping function
            org_variations = self._get_organization_variations(organization)
            
            print(f"🏢 Organization variations for '{organization}': {org_variations}")
            
            # Create comprehensive organization filter including custom fields
            # Use correct syntax for object-type custom fields (= instead of ~)
            org_conditions = []
            
            # Search in the key organization custom fields with all variations
            for variation in org_variations:
                org_conditions.extend([
                    f'cf[10032] = "{variation}"',   # Customer field - use = for object fields
                    f'cf[13400] = "{variation}"',   # Organizations field - use = for object fields
                ])
            
            # Also search in summary and description with key variations
            key_variations = org_variations[:5]  # Use top 5 variations to keep query manageable
            for variation in key_variations:
                org_conditions.extend([
                    f'summary ~ "{variation}"',     # Text fields - use ~ for contains
                    f'description ~ "{variation}"'  # Text fields - use ~ for contains
                ])
            
            org_filter = f'({" OR ".join(org_conditions)})'
            
            # Enhanced query filter to search in more fields
            query_filter = f'(text ~ "{query}" OR summary ~ "{query}" OR description ~ "{query}" OR comment ~ "{query}")'
            
            # Combine with priority for resolved tickets (they likely have solutions)
            jql_query = f'{org_filter} AND {query_filter} ORDER BY resolved DESC, updated DESC'
            
            print(f"🔍 JQL Query: {jql_query}")
            
            # Prepare search parameters for GET request
            fields = [
                'summary',
                'description', 
                'status',
                'priority',
                'assignee',
                'reporter',
                'created',
                'updated',
                'labels',
                'components',
                'issuetype',
                'project',
                'resolution',
                'resolutiondate',
                'comment',
                'customfield_10032',  # Customer field
                'customfield_13400',  # Organizations field  
                'customfield_24663'   # Organization field
            ]
            
            params = {
                'jql': jql_query,
                'maxResults': limit,
                'fields': ','.join(fields),
                'expand': 'changelog,renderedFields,comment'
            }
            
            response = self.session.get(
                f"{self.base_url}search/jql",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = []
                
                for issue in data.get('issues', []):
                    fields = issue.get('fields', {})
                    
                    # Extract comments for resolution steps
                    comments = []
                    if 'comment' in fields and fields['comment']:
                        comment_data = fields['comment']
                        
                        for comment in comment_data.get('comments', []):
                            comment_body_raw = comment.get('body', '')
                            comment_body = self._extract_text_from_adf(comment_body_raw)
                            comment_author = comment.get('author', {}).get('displayName', 'Unknown')
                            comment_created = comment.get('created', '')
                            
                            comments.append({
                                'author': comment_author,
                                'body': comment_body,
                                'created': comment_created
                            })
                    
                    # Extract resolution information
                    resolution_info = ""
                    if fields.get('resolution'):
                        res = fields['resolution']
                        resolution_name = res.get('name', '')
                        resolution_desc = res.get('description', '')
                        resolution_info = f"{resolution_name}"
                        if resolution_desc and resolution_desc != resolution_name:
                            resolution_info += f": {resolution_desc}"
                    
                    description_raw = fields.get('description', '') or ''
                    description = self._extract_text_from_adf(description_raw)
                    
                    # Create AI-powered resolution summary from ALL comments
                    comments_text = ""
                    resolution_summary = ""
                    
                    if comments:
                        # Collect all comments for AI analysis
                        all_comments_text = ""
                        for comment in comments:
                            comment_body = comment.get('body', '')  # Already extracted as plain text
                            comment_author = comment.get('author', 'Unknown')
                            comment_date = comment.get('created', '')
                            all_comments_text += f"\n[{comment_author} - {comment_date}]: {comment_body}\n"
                        
                        # Use AWS Bedrock AI to extract comprehensive resolution steps from all comments
                        if all_comments_text.strip():
                            try:
                                issue_summary = fields.get('summary', '')
                                issue_desc = description if description else ''
                                
                                resolution_summary = self._extract_resolution_with_ai(
                                    all_comments_text, 
                                    issue.get('key', ''),
                                    issue_summary,
                                    issue_desc
                                )
                                
                                if resolution_summary:
                                    comments_text = resolution_summary
                                else:
                                    # Fallback to enhanced rule-based extraction
                                    comments_text = self._rule_based_resolution_extraction(all_comments_text)
                                    
                            except Exception as e:
                                print(f"⚠️ AI resolution extraction failed for {issue.get('key', '')}: {e}")
                                # Fallback to recent comments
                                comments_text = self._fallback_comments_extraction(comments)
                    
                    full_content = str(description) + str(comments_text)
                    
                    issue_data = {
                        'key': issue.get('key', ''),
                        'summary': fields.get('summary', ''),
                        'description': description,
                        'content': full_content,
                        'status': fields.get('status', {}).get('name', ''),
                        'priority': fields.get('priority', {}).get('name', ''),
                        'assignee': fields.get('assignee', {}).get('displayName', '') if fields.get('assignee') else 'Unassigned',
                        'reporter': fields.get('reporter', {}).get('displayName', ''),
                        'created': fields.get('created', ''),
                        'updated': fields.get('updated', ''),
                        'labels': fields.get('labels', []),
                        'components': [comp.get('name', '') for comp in fields.get('components', [])],
                        'issuetype': fields.get('issuetype', {}).get('name', ''),
                        'project': fields.get('project', {}).get('key', ''),
                        'resolution': resolution_info,
                        'resolutiondate': fields.get('resolutiondate', ''),
                        'comments': comments,
                        'organization_match': organization  # Track which org this was matched for
                    }
                    
                    issues.append(issue_data)
                
                return issues
            else:
                print(f"❌ JIRA API error: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching JIRA for organization {organization}: {e}")
            return []

    def _extract_resolution_with_ai(self, comments_text: str, ticket_key: str, issue_summary: str = "", issue_description: str = "") -> str:
        """
        Use AWS Bedrock AI to extract resolution steps from all comments
        
        Args:
            comments_text: All comments combined
            ticket_key: JIRA ticket key for logging
            issue_summary: JIRA ticket summary
            issue_description: JIRA ticket description
            
        Returns:
            AI-extracted resolution summary with comprehensive steps
        """
        try:
            import boto3
            import json
            from botocore.exceptions import ClientError
            
            # Initialize Bedrock client
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            
            # Create a comprehensive prompt for resolution extraction
            prompt = f"""
            You are an expert technical support analyst. Analyze the following JIRA ticket and extract a comprehensive resolution summary.

            TICKET: {ticket_key}
            SUMMARY: {issue_summary}
            DESCRIPTION: {issue_description}

            ALL COMMENTS:
            {comments_text}

            Please provide a clear, step-by-step resolution summary that includes:
            1. Root cause analysis (if mentioned)
            2. Detailed solution steps 
            3. Any workarounds provided
            4. Verification steps
            5. Prevention measures (if any)

            Format your response as a structured solution with clear headings and numbered steps where appropriate.
            Focus on actionable information that would help someone resolve the same issue.

            If no clear resolution is found, state that explicitly and summarize what troubleshooting was attempted.
            """

            # Prepare the request for Claude model
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            }

            # Make the Bedrock API call
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and response_body['content']:
                ai_summary = response_body['content'][0]['text']
                return f"\n\n--- AI-EXTRACTED RESOLUTION SUMMARY ---\n{ai_summary}"
            else:
                return self._rule_based_resolution_extraction(comments_text)
                
        except ClientError as e:
            print(f"⚠️ AWS Bedrock error for {ticket_key}: {e}")
            return self._rule_based_resolution_extraction(comments_text)
        except Exception as e:
            print(f"⚠️ Error with Bedrock resolution extraction for {ticket_key}: {e}")
            return self._rule_based_resolution_extraction(comments_text)

    def _rule_based_resolution_extraction(self, comments_text: str) -> str:
        """
        Enhanced rule-based resolution extraction from comments
        
        Args:
            comments_text: All comments combined
            
        Returns:
            Extracted resolution steps
        """
        try:
            # Split into individual comments
            comment_blocks = comments_text.split('\n[')
            if not comment_blocks:
                return ""
            
            # Enhanced patterns for resolution detection
            resolution_patterns = [
                # Direct resolution indicators
                r'(?:resolved|fixed|solved|issue.{0,20}resolved|problem.{0,20}solved)',
                r'(?:solution|workaround|fix applied|steps taken)',
                r'(?:root cause|identified.{0,30}cause)',
                
                # Action indicators
                r'(?:implemented|updated|configured|restarted|rebooted)',
                r'(?:changed|modified|adjusted|corrected)',
                r'(?:installed|deployed|patched)',
                
                # Step indicators
                r'(?:follow.{0,10}steps|procedure|method)',
                r'(?:step \d+|1\.|2\.|3\.|\d+\.)',
                r'(?:first|second|third|next|then|finally)',
                
                # Resolution outcomes
                r'(?:working.{0,20}now|issue.{0,10}closed|ticket.{0,10}resolved)',
                r'(?:confirmed.{0,20}fix|verified.{0,20}solution)'
            ]
            
            resolution_content = []
            step_content = []
            
            # Analyze each comment
            for comment_block in comment_blocks:
                if not comment_block.strip():
                    continue
                    
                comment_lower = comment_block.lower()
                
                # Check for resolution patterns
                resolution_score = 0
                for pattern in resolution_patterns:
                    import re
                    if re.search(pattern, comment_lower):
                        resolution_score += 1
                
                # If comment has resolution indicators, include it
                if resolution_score >= 1:
                    # Clean up the comment
                    clean_comment = comment_block.strip()
                    if clean_comment.startswith('['):
                        # Extract just the content after author/date
                        parts = clean_comment.split(']: ', 1)
                        if len(parts) > 1:
                            clean_comment = parts[1]
                    
                    # Check if it contains step-like content
                    if any(re.search(r'(?:step \d+|\d+\.)', clean_comment.lower()) for pattern in [r'(?:step \d+|\d+\.)']):
                        step_content.append(clean_comment)
                    else:
                        resolution_content.append(clean_comment)
            
            # Build the resolution summary
            summary_parts = []
            
            if step_content:
                summary_parts.append("**Resolution Steps:**")
                for i, step in enumerate(step_content[:5], 1):  # Limit to 5 steps
                    summary_parts.append(f"{i}. {step[:200]}...")  # Truncate long steps
            
            if resolution_content:
                summary_parts.append("\n**Additional Resolution Information:**")
                for content in resolution_content[:3]:  # Limit to 3 additional items
                    summary_parts.append(f"• {content[:150]}...")
            
            if summary_parts:
                return "\n".join(summary_parts)
            else:
                return "No clear resolution steps found in comments."
                
        except Exception as e:
            print(f"⚠️ Rule-based extraction error: {e}")
            return ""

    def _fallback_comments_extraction(self, comments: List[Dict]) -> str:
        """
        Fallback method to extract recent comments if AI fails
        
        Args:
            comments: List of comment dictionaries
            
        Returns:
            Formatted recent comments
        """
        try:
            if not comments:
                return ""
            
            comments_text = "\n\n--- RECENT COMMENTS ---\n"
            # Get last 3 comments
            recent_comments = comments[-3:] if len(comments) > 3 else comments
            
            for comment in recent_comments:
                author = comment.get('author', 'Unknown')
                body = comment.get('body', '')  # Already extracted as plain text
                
                comments_text += f"\n💬 [{author}]: {body[:200]}...\n"
            
            return comments_text
            
        except Exception as e:
            print(f"⚠️ Fallback extraction error: {e}")
            return ""

    def search_issues(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search JIRA issues using JQL query
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of JIRA issues
        """
        try:
            if not self.test_connection():
                print("❌ JIRA connection not available")
                return []
            
            # Build JQL query
            jql_query = f'text ~ "{query}" OR summary ~ "{query}" OR description ~ "{query}"'
            
            # Prepare search parameters for GET request
            fields = [
                'summary',
                'description', 
                'status',
                'priority',
                'assignee',
                'reporter',
                'created',
                'updated',
                'labels',
                'components',
                'issuetype',
                'project',
                'resolution',
                'resolutiondate',
                'comment'
            ]
            
            params = {
                'jql': jql_query,
                'maxResults': limit,
                'fields': ','.join(fields),
                'expand': 'changelog,renderedFields,comment'
            }
            
            response = self.session.get(
                f"{self.base_url}search/jql",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = []
                
                for issue in data.get('issues', []):
                    fields = issue.get('fields', {})
                    
                    # Extract comments for resolution steps - get ALL comments
                    comments = []
                    if 'comment' in fields and fields['comment']:
                        comment_data = fields['comment']
                        # Check if there are more comments than returned
                        total_comments = comment_data.get('total', 0)
                        max_results = comment_data.get('maxResults', 0)
                        
                        for comment in comment_data.get('comments', []):
                            comment_body_raw = comment.get('body', '')
                            comment_body = self._extract_text_from_adf(comment_body_raw)
                            comment_author = comment.get('author', {}).get('displayName', 'Unknown')
                            comment_created = comment.get('created', '')
                            comments.append({
                                'author': comment_author,
                                'body': comment_body,
                                'created': comment_created
                            })
                        
                        # If comments are truncated, try to get issue individually for full comments
                        if total_comments > max_results and total_comments > len(comments):
                            issue_key = issue.get('key', '')
                            if issue_key:
                                # Get full issue details for complete comments
                                full_issue = self.get_issue(issue_key)
                                if full_issue and full_issue.get('all_comments'):
                                    comments = full_issue['all_comments']
                    
                    # Extract resolution information with more detail
                    resolution_info = ""
                    if fields.get('resolution'):
                        res = fields['resolution']
                        resolution_name = res.get('name', '')
                        resolution_desc = res.get('description', '')
                        resolution_info = f"{resolution_name}"
                        if resolution_desc and resolution_desc != resolution_name:
                            resolution_info += f": {resolution_desc}"
                    
                    # Check changelog for resolution details
                    changelog_resolution = ""
                    if 'changelog' in issue:
                        changelog = issue['changelog']
                        for history in changelog.get('histories', []):
                            for item in history.get('items', []):
                                if item.get('field') == 'resolution' and item.get('toString'):
                                    author = history.get('author', {}).get('displayName', 'Unknown')
                                    created = history.get('created', '')
                                    resolution_change = item.get('toString', '')
                                    changelog_resolution += f"\n[Resolved by {author} on {created[:10]}]: {resolution_change}"
                    
                    # Combine description and comments for comprehensive content
                    description_raw = fields.get('description', '') or ''
                    description = self._extract_text_from_adf(description_raw)
                    
                    comments_text = ""
                    if comments:
                        comments_text = "\n\n--- RESOLUTION STEPS & COMMENTS ---\n"
                        # Prioritize comments that likely contain resolution info
                        resolution_keywords = ['resolution', 'resolved', 'fixed', 'solution', 'workaround', 'steps', 'fix']
                        resolution_comments = []
                        other_comments = []
                        
                        for comment in comments:
                            comment_body = comment.get('body', '')
                            if isinstance(comment_body, dict):
                                comment_body = str(comment_body)
                            comment_body_lower = comment_body.lower()
                            
                            # Check if comment likely contains resolution info
                            if any(keyword in comment_body_lower for keyword in resolution_keywords):
                                resolution_comments.append(comment)
                            else:
                                other_comments.append(comment)
                        
                        # Show resolution comments first, then others (limit total)
                        priority_comments = resolution_comments[-3:] + other_comments[-2:]  # Last 3 resolution + 2 others
                        
                        for comment in priority_comments[-5:]:  # Total limit of 5 comments
                            comment_body = comment.get('body', '')
                            if isinstance(comment_body, dict):
                                comment_body = str(comment_body)
                            comments_text += f"\n[{comment['author']}]: {comment_body}\n"
                    
                    full_content = str(description) + str(comments_text)
                    
                    # Add resolution information
                    if resolution_info:
                        full_content += f"\n\n--- RESOLUTION ---\n{resolution_info}"
                    if changelog_resolution:
                        full_content += f"\n\n--- RESOLUTION HISTORY ---\n{changelog_resolution}"
                    
                    # Extract issue data
                    issue_data = {
                        'key': issue.get('key', ''),
                        'title': fields.get('summary', ''),
                        'content': full_content,
                        'description': description,
                        'comments': comments,
                        'resolution': resolution_info,
                        'status': fields.get('status', {}).get('name', '') if fields.get('status') else '',
                        'priority': fields.get('priority', {}).get('name', '') if fields.get('priority') else '',
                        'assignee': fields.get('assignee', {}).get('displayName', '') if fields.get('assignee') else 'Unassigned',
                        'reporter': fields.get('reporter', {}).get('displayName', '') if fields.get('reporter') else '',
                        'created': fields.get('created', ''),
                        'updated': fields.get('updated', ''),
                        'resolution_date': fields.get('resolutiondate', ''),
                        'labels': fields.get('labels', []),
                        'components': [comp.get('name', '') for comp in fields.get('components', [])],
                        'issue_type': fields.get('issuetype', {}).get('name', '') if fields.get('issuetype') else '',
                        'project': fields.get('project', {}).get('key', '') if fields.get('project') else '',
                        'url': f"{self.base_url.replace('/rest/api/3/', '')}/browse/{issue.get('key', '')}"
                    }
                    
                    issues.append(issue_data)
                
                print(f"✅ Found {len(issues)} JIRA issues")
                return issues
            else:
                print(f"❌ JIRA search failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching JIRA: {e}")
            return []
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific JIRA issue by key
        
        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")
            
        Returns:
            Issue details or None if not found
        """
        try:
            if not self.test_connection():
                print("❌ JIRA connection not available")
                return None
            
            response = self.session.get(
                f"{self.base_url}issue/{issue_key}",
                params={'expand': 'changelog,comments'},
                timeout=30
            )
            
            if response.status_code == 200:
                issue = response.json()
                fields = issue.get('fields', {})
                
                # Get all comments
                all_comments = []
                if 'comment' in fields and fields['comment']:
                    for comment in fields['comment'].get('comments', []):
                        comment_body = comment.get('body', '')
                        comment_author = comment.get('author', {}).get('displayName', 'Unknown')
                        comment_created = comment.get('created', '')
                        all_comments.append({
                            'author': comment_author,
                            'body': comment_body,
                            'created': comment_created
                        })
                
                return {
                    'key': issue.get('key', ''),
                    'title': fields.get('summary', ''),
                    'content': fields.get('description', '') or '',
                    'all_comments': all_comments,
                    'status': fields.get('status', {}).get('name', '') if fields.get('status') else '',
                    'priority': fields.get('priority', {}).get('name', '') if fields.get('priority') else '',
                    'assignee': fields.get('assignee', {}).get('displayName', '') if fields.get('assignee') else 'Unassigned',
                    'reporter': fields.get('reporter', {}).get('displayName', '') if fields.get('reporter') else '',
                    'created': fields.get('created', ''),
                    'updated': fields.get('updated', ''),
                    'labels': fields.get('labels', []),
                    'components': [comp.get('name', '') for comp in fields.get('components', [])],
                    'issue_type': fields.get('issuetype', {}).get('name', '') if fields.get('issuetype') else '',
                    'project': fields.get('project', {}).get('key', '') if fields.get('project') else '',
                    'url': f"{self.base_url.replace('/rest/api/3/', '')}/browse/{issue.get('key', '')}"
                }
            else:
                print(f"❌ Failed to get JIRA issue {issue_key}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting JIRA issue: {e}")
            return None
    
    def create_issue(self, project_key: str, summary: str, issue_type: str = "Task", 
                    description: str = "", priority: str = "Medium", 
                    assignee: str = None, labels: List[str] = None) -> Optional[str]:
        """
        Create a new JIRA issue
        
        Args:
            project_key: JIRA project key
            summary: Issue summary
            issue_type: Type of issue (Task, Bug, Story, etc.)
            description: Issue description
            priority: Issue priority
            assignee: Assignee username/email
            labels: List of labels
            
        Returns:
            Created issue key or None if failed
        """
        try:
            if not self.test_connection():
                print("❌ JIRA connection not available")
                return None
            
            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type},
                    "priority": {"name": priority}
                }
            }
            
            if assignee:
                payload["fields"]["assignee"] = {"name": assignee}
            
            if labels:
                payload["fields"]["labels"] = labels
            
            response = self.session.post(
                f"{self.base_url}issue",
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 201:
                created_issue = response.json()
                issue_key = created_issue.get('key')
                print(f"✅ Created JIRA issue: {issue_key}")
                return issue_key
            else:
                print(f"❌ Failed to create JIRA issue: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating JIRA issue: {e}")
            return None
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of available JIRA projects"""
        try:
            if not self.test_connection():
                return []
            
            response = self.session.get(f"{self.base_url}project", timeout=30)
            
            if response.status_code == 200:
                projects = response.json()
                return [
                    {
                        'key': project.get('key', ''),
                        'name': project.get('name', ''),
                        'description': project.get('description', ''),
                        'project_type': project.get('projectTypeKey', '')
                    }
                    for project in projects
                ]
            else:
                print(f"❌ Failed to get JIRA projects: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting JIRA projects: {e}")
            return []