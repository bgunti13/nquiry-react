"""
Azure Blob Storage Tool for nquiry Integration
Ready-to-use SharePoint document search and retrieval
"""

import requests
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import mimetypes
import io
import re
from datetime import datetime

# Content extraction libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class AzureBlobSharePointTool:
    """
    Tool for searching and retrieving SharePoint documents from Azure Blob Storage
    Integrates with nquiry's intelligent query processing system
    """
    
    def __init__(self):
        # Configuration from config.py
        from config import (AZURE_STORAGE_ACCOUNT, AZURE_CONTAINER_NAME, 
                           AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
        
        self.tenant_id = AZURE_TENANT_ID
        self.client_id = AZURE_CLIENT_ID
        self.client_secret = AZURE_CLIENT_SECRET
        self.storage_account = AZURE_STORAGE_ACCOUNT
        self.container_name = AZURE_CONTAINER_NAME
        self.token = None
        self.token_expires = None
        
    def authenticate(self) -> bool:
        """Get access token for Azure storage"""
        try:
            resp = requests.post(
                url=f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://storage.azure.com/.default"
                }
            )
            
            if resp.status_code == 200:
                token_data = resp.json()
                self.token = token_data['access_token']
                return True
            else:
                print(f"Authentication failed: {resp.text}")
                return False
                
        except Exception as e:
            print(f"Error during authentication: {e}")
            return False
    
    def search_documents(self, query: str, file_types: List[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Enhanced search for documents in SharePoint with content extraction
        
        Args:
            query: Search query string
            file_types: Optional list of file extensions to filter by
            max_results: Maximum number of results to return (default 10)
            
        Returns:
            List of matching documents with metadata and content relevance
        """
        if not self.token and not self.authenticate():
            return []

        # Fast search strategy for production:
        # 1. Quick filename filtering first
        # 2. Prioritize workbench/procedure-related documents
        # 3. Smart content extraction only for promising candidates

        all_blobs = self._list_all_blobs()
        matching_docs = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        # Priority keywords for workbench/procedure content
        priority_keywords = ['workbench', 'upload', 'procedure', 'guide', 'how to', 'validation', 'manual', 'instruction']
        
        # Phase 1: Quick filename scan with priority scoring
        filename_candidates = []
        for blob in all_blobs:
            blob_name = blob.get('name', '').lower()
            original_name = blob.get('name', '')

            # Filter by file type if specified
            if file_types:
                file_ext = blob_name.split('.')[-1] if '.' in blob_name else ''
                if file_ext not in [ft.lower().lstrip('.') for ft in file_types]:
                    continue

            # Enhanced filename relevance scoring
            filename_score = 0
            
            # Exact query match gets highest score
            if query_lower in blob_name:
                filename_score += 10.0
            
            # Priority keyword matches
            for keyword in priority_keywords:
                if keyword in blob_name:
                    filename_score += 3.0
                    
            # Individual term matches
            for term in query_terms:
                if term in blob_name:
                    filename_score += 2.0
            
            # Boost for procedure/documentation files
            if any(doc_type in blob_name for doc_type in ['.docx', '.pdf', '.doc']):
                filename_score += 1.0

            if filename_score > 0:
                filename_candidates.append((blob, filename_score, original_name))

        # Sort filename candidates by relevance (highest first)
        filename_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Phase 2: Content extraction for top candidates only
        candidates_to_check = min(30, len(filename_candidates))  # Check more candidates
        
        for i, (blob, filename_score, original_name) in enumerate(filename_candidates[:candidates_to_check]):
            blob_name = blob.get('name', '').lower()
            
            # Smart content extraction - prioritize high-scoring files
            document_content = ""
            content_match = False
            
            # Extract content for promising files (higher threshold for content extraction)
            should_extract = (
                filename_score >= 3.0 or  # High filename relevance
                any(keyword in blob_name for keyword in priority_keywords) or
                any(ext in blob_name for ext in ['.docx', '.pdf', '.txt', '.doc'])
            )
            
            if should_extract:
                try:
                    document_content = self._extract_document_content(blob)
                    if document_content:
                        content_lower = document_content.lower()
                        content_match = (
                            query_lower in content_lower or
                            any(term in content_lower for term in query_terms) or
                            any(keyword in content_lower for keyword in priority_keywords)
                        )
                except Exception:
                    pass  # Continue without content if extraction fails

            # Calculate final relevance with content boost
            total_relevance = filename_score
            if content_match:
                content_score = self._calculate_content_relevance(query_lower, blob_name, document_content)
                total_relevance += content_score
                
            # Only include documents with meaningful relevance
            if total_relevance >= 2.0:  # Minimum threshold
                match_type = []
                if filename_score > 0:
                    match_type.append("filename")
                if content_match:
                    match_type.append("content")

                matching_docs.append({
                    'name': original_name,
                    'path': blob.get('path', ''),
                    'size': blob.get('size', 0),
                    'modified': blob.get('last_modified'),
                    'url': self._get_blob_url(original_name),
                    'content': document_content[:400] if document_content else '',
                    'match_type': " + ".join(match_type) if match_type else "filename",
                    'relevance_score': total_relevance
                })

            # Early termination if we have enough high-quality results
            if len([d for d in matching_docs if d['relevance_score'] >= 5.0]) >= max_results:
                break

        # Sort by relevance and return top results
        matching_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return matching_docs[:max_results]

    def _extract_document_content(self, blob: Dict[str, Any]) -> str:
        """
        Extract text content from document files
        
        Args:
            blob: Blob metadata dictionary
            
        Returns:
            Extracted text content or empty string
        """
        blob_name = blob.get('name', '')
        file_extension = blob_name.lower().split('.')[-1] if '.' in blob_name else ''
        
        try:
            # Download blob content
            blob_url = self._get_blob_url(blob_name)
            headers = {
                'Authorization': f'Bearer {self.token}',
                'x-ms-version': '2020-04-08'
            }
            
            response = requests.get(blob_url, headers=headers)
            if response.status_code != 200:
                return ""
            
            content_bytes = response.content
            
            # Extract based on file type
            if file_extension == 'txt' or file_extension == 'md':
                return self._extract_text_content_simple(content_bytes)
            elif file_extension == 'pdf':
                return self._extract_pdf_content(content_bytes)
            elif file_extension == 'docx':
                return self._extract_docx_content(content_bytes)
            else:
                # Try to extract as text for unknown types
                return self._extract_text_content_simple(content_bytes)
                
        except Exception as e:
            print(f"⚠️ Content extraction error for {blob_name}: {e}")
            return ""
    
    def _extract_text_content_simple(self, content_bytes: bytes) -> str:
        """Extract content from plain text files"""
        try:
            # Try UTF-8 first, then other encodings
            encodings = ['utf-8', 'utf-16', 'latin1', 'cp1252']
            for encoding in encodings:
                try:
                    return content_bytes.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception:
            return ""
    
    def _extract_pdf_content(self, content_bytes: bytes) -> str:
        """Extract text content from PDF files"""
        if not PDF_AVAILABLE:
            return ""
            
        try:
            pdf_file = io.BytesIO(content_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page_num in range(min(len(pdf_reader.pages), 10)):  # Limit to first 10 pages
                page = pdf_reader.pages[page_num]
                text_content.append(page.extract_text())
            
            return "\n".join(text_content)
        except Exception as e:
            return ""
    
    def _extract_docx_content(self, content_bytes: bytes) -> str:
        """Extract text content from DOCX files"""
        if not DOCX_AVAILABLE:
            return ""
            
        try:
            docx_file = io.BytesIO(content_bytes)
            doc = DocxDocument(docx_file)
            
            text_content = []
            for paragraph in doc.paragraphs:
                text_content.append(paragraph.text)
            
            return "\n".join(text_content)
        except Exception as e:
            return ""
    
    def _calculate_content_relevance(self, query: str, filename: str, content: str) -> float:
        """
        Calculate relevance score based on both filename and content matches
        
        Args:
            query: Search query (lowercase)
            filename: Blob filename (lowercase)
            content: Extracted content (any case)
            
        Returns:
            Relevance score (higher = more relevant)
        """
        score = 0.0
        query_terms = query.split()
        content_lower = content.lower() if content else ""
        
        # Filename matches (higher weight)
        for term in query_terms:
            if term in filename:
                score += 2.0
        
        # Exact query match in filename
        if query in filename:
            score += 5.0
        
        # Content matches
        if content:
            for term in query_terms:
                # Count occurrences in content
                term_count = content_lower.count(term)
                score += term_count * 0.5
            
            # Exact query match in content
            if query in content_lower:
                score += 3.0
            
            # Bonus for content length (more content = potentially more relevant)
            score += min(len(content) / 1000, 1.0)
        
        return score
    
    def get_document_content(self, blob_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document content for analysis
        
        Args:
            blob_path: Path to the blob in storage
            
        Returns:
            Document content and metadata
        """
        if not self.token and not self.authenticate():
            return None
        
        try:
            url = f"https://{self.storage_account}.blob.core.windows.net/{self.container_name}/{blob_path}"
            
            response = requests.get(url, headers={
                "Authorization": f"Bearer {self.token}",
                "x-ms-version": "2023-11-03"
            })
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                return {
                    'content': response.content,
                    'content_type': content_type,
                    'size': len(response.content),
                    'text_content': self._extract_text_content(response.content, content_type),
                    'metadata': {
                        'last_modified': response.headers.get('last-modified'),
                        'etag': response.headers.get('etag'),
                        'content_encoding': response.headers.get('content-encoding')
                    }
                }
            else:
                print(f"Failed to get document {blob_path}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error retrieving document {blob_path}: {e}")
            return None
    
    def get_sharepoint_structure(self) -> Dict[str, Any]:
        """
        Get the current SharePoint structure for navigation
        
        Returns:
            Hierarchical structure of SharePoint sites and documents
        """
        if not self.token and not self.authenticate():
            return {}
        
        # Use the tree generator logic
        from generate_sharepoint_tree import AzureBlobTreeGenerator
        
        generator = AzureBlobTreeGenerator()
        generator.token = self.token  # Reuse our token
        
        return generator.build_directory_tree()
    
    def _list_all_blobs(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List all blobs with metadata"""
        try:
            url = f"https://{self.storage_account}.blob.core.windows.net/{self.container_name}"
            params = {
                "restype": "container",
                "comp": "list",
                "include": "metadata",
                "maxresults": "5000"
            }
            
            if prefix:
                params["prefix"] = prefix
            
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_string}"
            
            response = requests.get(full_url, headers={
                "Authorization": f"Bearer {self.token}",
                "x-ms-version": "2023-11-03"
            })
            
            if response.status_code == 200:
                return self._parse_blob_list(response.text)
            else:
                print(f"Failed to list blobs: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error listing blobs: {e}")
            return []
    
    def _parse_blob_list(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse blob list XML response"""
        blobs = []
        try:
            root = ET.fromstring(xml_content)
            
            # Try both namespace and non-namespace patterns
            blob_patterns = [
                './/Blob',  # Non-namespace
                './/{http://schemas.microsoft.com/windowsazure}Blob'  # With namespace
            ]
            
            blob_elements = []
            for pattern in blob_patterns:
                blob_elements = root.findall(pattern)
                if blob_elements:
                    break
            
            for i, blob_elem in enumerate(blob_elements):
                try:
                    # Get blob name and properties
                    name_elem = blob_elem.find('Name')
                    properties = blob_elem.find('Properties')
                    
                    if name_elem is not None and name_elem.text:
                        blob_data = {
                            'name': name_elem.text,
                            'path': name_elem.text,
                        }
                        
                        if properties is not None:
                            # Extract properties - use direct child searches
                            size_elem = (properties.find('Content-Length') or 
                                       properties.find('.//{http://schemas.microsoft.com/windowsazure}Content-Length'))
                            modified_elem = (properties.find('Last-Modified') or 
                                           properties.find('.//{http://schemas.microsoft.com/windowsazure}Last-Modified'))
                            type_elem = (properties.find('Content-Type') or 
                                       properties.find('.//{http://schemas.microsoft.com/windowsazure}Content-Type'))
                            resource_type_elem = (properties.find('ResourceType') or 
                                                properties.find('.//{http://schemas.microsoft.com/windowsazure}ResourceType'))
                            
                            if size_elem is not None and size_elem.text:
                                try:
                                    blob_data['size'] = int(size_elem.text)
                                except ValueError:
                                    blob_data['size'] = 0
                            else:
                                blob_data['size'] = 0
                                
                            if modified_elem is not None:
                                blob_data['last_modified'] = modified_elem.text
                            if type_elem is not None:
                                blob_data['content_type'] = type_elem.text
                            if resource_type_elem is not None:
                                blob_data['resource_type'] = resource_type_elem.text
                        
                        # Include all blob types (files and directories)
                        blobs.append(blob_data)
                        
                except Exception as e:
                    print(f"   ❌ Error processing blob {i+1}: {e}")
                    
        except ET.ParseError as e:
            print(f"❌ Error parsing blob list XML: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in blob parsing: {e}")
            import traceback
            traceback.print_exc()
        
        return blobs
    
    def _get_blob_url(self, blob_path: str) -> str:
        """Generate blob URL"""
        return f"https://{self.storage_account}.blob.core.windows.net/{self.container_name}/{blob_path}"
    
    def _calculate_relevance(self, query: str, blob_name: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_terms = query.split()
        
        # Exact match bonus
        if query in blob_name:
            score += 10.0
        
        # Term match scoring
        for term in query_terms:
            if term in blob_name:
                score += 5.0
        
        # File type bonuses
        if blob_name.endswith(('.pdf', '.doc', '.docx')):
            score += 2.0
        elif blob_name.endswith(('.txt', '.md')):
            score += 1.0
        
    def _calculate_relevance(self, query: str, filename: str) -> float:
        """
        Calculate relevance score for search results (legacy method)
        
        Args:
            query: Search query
            filename: Blob filename
            
        Returns:
            Relevance score
        """
        score = 0
        query_terms = query.split()
        
        # Exact match gets highest score
        if query in filename:
            score += 10
        
        # Individual term matches
        for term in query_terms:
            if term in filename:
                score += 1
        
        return score
    
    def _extract_text_content(self, content: bytes, content_type: str) -> str:
        """Extract text content from documents for search"""
        try:
            # For text files
            if 'text/' in content_type:
                return content.decode('utf-8', errors='ignore')
            
            # For other file types, return basic info
            # (In production, you'd use libraries like PyPDF2, python-docx, etc.)
            return f"Binary content ({content_type})"
            
        except Exception as e:
            return f"Could not extract text: {e}"

# Integration function for nquiry main workflow
def search_sharepoint_documents(query: str) -> Dict[str, Any]:
    """
    Main function to integrate with nquiry workflow
    
    Args:
        query: User's search query
        
    Returns:
        Formatted response for nquiry
    """
    tool = AzureBlobSharePointTool()
    
    try:
        # Search for relevant documents
        documents = tool.search_documents(query)
        
        if not documents:
            return {
                "success": False,
                "message": "No SharePoint documents found matching your query.",
                "documents": []
            }
        
        # Format response
        response = {
            "success": True,
            "message": f"Found {len(documents)} relevant SharePoint documents:",
            "documents": documents,
            "total_found": len(documents)
        }
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error searching SharePoint: {str(e)}",
            "documents": []
        }

# Example usage for testing
if __name__ == "__main__":
    # Test the tool
    tool = AzureBlobSharePointTool()
    
    if tool.authenticate():
        print("✅ Authentication successful")
        
        # Test search
        results = tool.search_documents("project documentation")
        print(f"Found {len(results)} documents")
        
        # Test structure
        structure = tool.get_sharepoint_structure()
        print(f"Structure has {len(structure)} elements")
    else:
        print("❌ Authentication failed")