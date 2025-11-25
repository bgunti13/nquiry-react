"""
Image Analysis Service using AWS Bedrock Claude 3.5 Sonnet
Analyzes images to extract text, understand errors, and provide context for chatbot
"""

import boto3
import json
import base64
from typing import List, Dict, Optional, Tuple
from config import AWS_REGION, BEDROCK_IMAGE_MODEL
import os
from dotenv import load_dotenv

load_dotenv()

class ImageAnalyzer:
    """Service for analyzing images using AWS Bedrock Vision models"""
    
    def __init__(self):
        """Initialize the image analyzer with Claude 3.5 Sonnet"""
        self.bedrock_client = self._create_bedrock_client()
        # Using Claude 3.5 Sonnet v2 which has excellent vision capabilities
        self.model_id = BEDROCK_IMAGE_MODEL
        
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
            print(f"❌ Error creating Bedrock client: {e}")
            return None

    def analyze_images_with_query(self, images: List[Dict], user_query: str = "") -> Dict:
        """
        Analyze images with user query context to extract relevant information
        
        Args:
            images: List of image data with base64 content
            user_query: User's question or description of the issue
            
        Returns:
            Dict with analysis results and extracted information
        """
        if not self.bedrock_client:
            return {
                "success": False,
                "error": "Bedrock client not initialized",
                "extracted_text": "",
                "analysis": ""
            }
            
        try:
            # Prepare the images for the API
            image_contents = []
            for i, image in enumerate(images):
                # Extract base64 data (remove data:image/jpeg;base64, prefix if present)
                base64_data = image.get('base64', '')
                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]
                    
                image_contents.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.get('type', 'image/jpeg'),
                        "data": base64_data
                    }
                })

            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(user_query, len(images))
            
            # Prepare message content with both text and images
            message_content = [{"type": "text", "text": analysis_prompt}] + image_contents

            # Prepare the request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                "temperature": 0.1  # Low temperature for more consistent analysis
            }

            # Call Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                analysis_text = response_body['content'][0]['text']
                
                # Parse the structured response
                parsed_analysis = self._parse_analysis_response(analysis_text)
                
                return {
                    "success": True,
                    "analysis": analysis_text,
                    "extracted_text": parsed_analysis.get("extracted_text", ""),
                    "issue_summary": parsed_analysis.get("issue_summary", ""),
                    "technical_details": parsed_analysis.get("technical_details", []),
                    "suggested_search_terms": parsed_analysis.get("suggested_search_terms", []),
                    "error_type": parsed_analysis.get("error_type", ""),
                    "raw_response": analysis_text
                }
            else:
                return {
                    "success": False,
                    "error": "No analysis content returned from model",
                    "extracted_text": "",
                    "analysis": ""
                }
                
        except Exception as e:
            print(f"❌ Error analyzing images: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "analysis": ""
            }

    def _create_analysis_prompt(self, user_query: str, image_count: int) -> str:
        """Create a comprehensive prompt for image analysis"""
        
        base_prompt = f"""
You are an expert technical support analyst with specialized skills in analyzing screenshots, error messages, and technical documentation from images.

USER'S QUESTION/CONTEXT: {user_query if user_query else "General analysis requested"}

Please analyze the provided {image_count} image(s) and provide a comprehensive analysis in the following structured format:

## EXTRACTED TEXT
[Extract and transcribe ALL visible text from the image(s), including error messages, UI labels, code snippets, file paths, etc.]

## ISSUE SUMMARY  
[Provide a clear, concise summary of the main issue or topic shown in the image(s)]

## TECHNICAL DETAILS
[List specific technical details like:]
- Error codes or messages
- File paths or locations
- Application/system information
- Stack traces or logs
- Configuration details
- Version numbers

## ERROR TYPE & SEVERITY
[Classify the type of error/issue if present:]
- Error category (e.g., Authentication, Network, Database, UI, etc.)
- Severity level (Critical, High, Medium, Low)
- Potential impact

## SUGGESTED SEARCH TERMS
[Provide 5-7 specific search terms that would help find solutions for this issue in knowledge bases, focusing on:]
- Key error messages
- Product/feature names
- Technical components
- Specific terminology from the images

## RECOMMENDATIONS
[Provide immediate actionable suggestions based on what you see]

If the images show error messages, focus heavily on extracting exact error text and identifying the root cause.
If the images show UI elements, describe the workflow or process being shown.
If the images contain code, explain what the code does and identify any potential issues.

Please be thorough and specific in your analysis.
"""
        
        return base_prompt

    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse the structured analysis response into components"""
        try:
            sections = {}
            current_section = None
            content_lines = []
            
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Check if this is a section header
                if line.startswith('##') and line.upper().replace('#', '').strip() in [
                    'EXTRACTED TEXT', 'ISSUE SUMMARY', 'TECHNICAL DETAILS', 
                    'ERROR TYPE & SEVERITY', 'SUGGESTED SEARCH TERMS', 'RECOMMENDATIONS'
                ]:
                    # Save previous section
                    if current_section:
                        sections[current_section] = '\n'.join(content_lines).strip()
                    
                    # Start new section
                    current_section = line.upper().replace('#', '').strip().lower().replace(' ', '_')
                    content_lines = []
                
                elif current_section and line:
                    content_lines.append(line)
            
            # Save last section
            if current_section:
                sections[current_section] = '\n'.join(content_lines).strip()
            
            # Extract specific components
            extracted_text = sections.get('extracted_text', '')
            issue_summary = sections.get('issue_summary', '')
            technical_details = sections.get('technical_details', '').split('\n') if sections.get('technical_details') else []
            
            # Parse search terms
            suggested_search_terms = []
            search_terms_text = sections.get('suggested_search_terms', '')
            if search_terms_text:
                # Extract terms from bullet points or numbered lists
                for line in search_terms_text.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or any(char.isdigit() for char in line[:3])):
                        # Remove bullet points and numbers
                        clean_term = line.lstrip('-•0123456789. ').strip()
                        if clean_term:
                            suggested_search_terms.append(clean_term)
            
            # Extract error type
            error_type = ""
            error_section = sections.get('error_type_&_severity', '')
            if error_section:
                # Look for error category
                for line in error_section.split('\n'):
                    if 'category' in line.lower() or 'type' in line.lower():
                        error_type = line.split(':')[-1].strip() if ':' in line else line
                        break
            
            return {
                "extracted_text": extracted_text,
                "issue_summary": issue_summary,
                "technical_details": [detail.strip() for detail in technical_details if detail.strip()],
                "suggested_search_terms": suggested_search_terms,
                "error_type": error_type,
                "recommendations": sections.get('recommendations', '')
            }
            
        except Exception as e:
            print(f"❌ Error parsing analysis response: {e}")
            return {
                "extracted_text": response_text,  # Fallback to raw text
                "issue_summary": "",
                "technical_details": [],
                "suggested_search_terms": [],
                "error_type": "",
                "recommendations": ""
            }

    def create_enhanced_query(self, original_query: str, image_analysis: Dict) -> str:
        """
        Create an enhanced query combining user input with image analysis
        
        Args:
            original_query: User's original question
            image_analysis: Results from image analysis
            
        Returns:
            Enhanced query string for better search results
        """
        if not image_analysis.get("success"):
            return original_query
            
        enhanced_parts = []
        
        # Start with original query if provided
        if original_query.strip():
            enhanced_parts.append(f"User Question: {original_query}")
        
        # Add extracted text from images
        extracted_text = image_analysis.get("extracted_text", "")
        if extracted_text:
            enhanced_parts.append(f"Error/Text from Image: {extracted_text}")
        
        # Add issue summary
        issue_summary = image_analysis.get("issue_summary", "")
        if issue_summary:
            enhanced_parts.append(f"Issue Description: {issue_summary}")
        
        # Add technical details
        technical_details = image_analysis.get("technical_details", [])
        if technical_details:
            enhanced_parts.append(f"Technical Details: {' | '.join(technical_details[:3])}")  # Limit to top 3
        
        # Combine all parts
        enhanced_query = "\n\n".join(enhanced_parts)
        
        return enhanced_query if enhanced_query.strip() else original_query

    def get_image_context_for_llm(self, image_analysis: Dict) -> str:
        """
        Create a context string from image analysis for LLM processing
        
        Args:
            image_analysis: Results from image analysis
            
        Returns:
            Formatted context string
        """
        if not image_analysis.get("success"):
            return "Image analysis failed or unavailable."
        
        context_parts = []
        
        context_parts.append("=== IMAGE ANALYSIS CONTEXT ===")
        
        # Issue summary
        if image_analysis.get("issue_summary"):
            context_parts.append(f"Issue: {image_analysis['issue_summary']}")
        
        # Extracted text
        if image_analysis.get("extracted_text"):
            context_parts.append(f"Text from Image: {image_analysis['extracted_text']}")
        
        # Error type
        if image_analysis.get("error_type"):
            context_parts.append(f"Error Type: {image_analysis['error_type']}")
        
        # Technical details
        technical_details = image_analysis.get("technical_details", [])
        if technical_details:
            context_parts.append(f"Technical Details: {'; '.join(technical_details[:5])}")
        
        context_parts.append("=== END IMAGE ANALYSIS ===")
        
        return "\n".join(context_parts)


# Create global instance
image_analyzer = ImageAnalyzer()