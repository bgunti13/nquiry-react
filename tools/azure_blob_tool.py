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
    
    def search_documents(self, query: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for documents in SharePoint based on query
        
        Args:
            query: Search query string
            file_types: Optional list of file extensions to filter by
            
        Returns:
            List of matching documents with metadata
        """
        if not self.token and not self.authenticate():
            return []
        
        # Search strategy:
        # 1. Get all blobs with metadata
        # 2. Filter by file type if specified
        # 3. Match query against file names and metadata
        
        all_blobs = self._list_all_blobs()
        matching_docs = []
        
        query_lower = query.lower()
        
        for blob in all_blobs:
            blob_name = blob.get('name', '').lower()
            
            # Filter by file type if specified
            if file_types:
                file_ext = blob_name.split('.')[-1] if '.' in blob_name else ''
                if file_ext not in [ft.lower().lstrip('.') for ft in file_types]:
                    continue
            
            # Simple text matching (can be enhanced with semantic search)
            if (query_lower in blob_name or 
                any(term in blob_name for term in query_lower.split())):
                
                matching_docs.append({
                    'name': blob.get('name'),
                    'path': blob.get('path', ''),
                    'size': blob.get('size', 0),
                    'modified': blob.get('last_modified'),
                    'url': self._get_blob_url(blob.get('name')),
                    'relevance_score': self._calculate_relevance(query_lower, blob_name)
                })
        
        # Sort by relevance
        matching_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return matching_docs[:10]  # Return top 10 matches
    
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
                "maxresults": "1000"
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
            blob_elements = root.findall('.//{http://schemas.microsoft.com/windowsazure}Blob')
            
            for blob_elem in blob_elements:
                name_elem = blob_elem.find('.//{http://schemas.microsoft.com/windowsazure}Name')
                properties = blob_elem.find('.//{http://schemas.microsoft.com/windowsazure}Properties')
                
                if name_elem is not None:
                    blob_data = {
                        'name': name_elem.text,
                        'path': name_elem.text,
                    }
                    
                    if properties is not None:
                        # Extract properties
                        size_elem = properties.find('.//{http://schemas.microsoft.com/windowsazure}Content-Length')
                        modified_elem = properties.find('.//{http://schemas.microsoft.com/windowsazure}Last-Modified')
                        type_elem = properties.find('.//{http://schemas.microsoft.com/windowsazure}Content-Type')
                        
                        if size_elem is not None:
                            blob_data['size'] = int(size_elem.text)
                        if modified_elem is not None:
                            blob_data['last_modified'] = modified_elem.text
                        if type_elem is not None:
                            blob_data['content_type'] = type_elem.text
                    
                    blobs.append(blob_data)
                    
        except ET.ParseError as e:
            print(f"Error parsing blob list: {e}")
        
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