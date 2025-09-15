"""
Semantic search module using sentence transformers and cosine similarity
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import VECTOR_STORE_PATH, SIMILARITY_THRESHOLD

class SemanticSearch:
    """
    Semantic search engine using sentence transformers and vector similarity
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        # Using a more powerful model for better semantic understanding
        self.model = SentenceTransformer(model_name)
        self.vector_store_path = VECTOR_STORE_PATH
        self.similarity_threshold = SIMILARITY_THRESHOLD
        self._ensure_vector_store_exists()
        
    def _ensure_vector_store_exists(self):
        """Create vector store directory if it doesn't exist"""
        if not os.path.exists(self.vector_store_path):
            os.makedirs(self.vector_store_path)
    
    def _get_vector_file_path(self, source: str) -> str:
        """Get the file path for storing vectors for a specific source"""
        return os.path.join(self.vector_store_path, f"{source.lower()}_vectors.pkl")
    
    def _get_documents_file_path(self, source: str) -> str:
        """Get the file path for storing documents for a specific source"""
        return os.path.join(self.vector_store_path, f"{source.lower()}_documents.pkl")
    
    def store_documents(self, documents: List[Dict], source: str):
        """
        Store documents and their embeddings for a specific source
        
        Args:
            documents: List of documents with 'content', 'title', and other metadata
            source: Source name (JIRA, CONFLUENCE, MINDTOUCH)
        """
        if not documents:
            return
        
        # Extract text content for embedding with enhanced context
        texts = []
        for doc in documents:
            # Combine title and content for better semantic representation
            title = doc.get('title', '')
            content = doc.get('content', '') or doc.get('summary', '') or doc.get('description', '')
            
            # Add additional context fields if available
            extra_fields = []
            if doc.get('labels'):
                labels = doc.get('labels', [])
                if isinstance(labels, list):
                    extra_fields.append(f"Labels: {', '.join(labels)}")
                else:
                    extra_fields.append(f"Labels: {labels}")
            
            if doc.get('status'):
                extra_fields.append(f"Status: {doc.get('status')}")
                
            if doc.get('priority'):
                extra_fields.append(f"Priority: {doc.get('priority')}")
            
            # Combine all text with enhanced context
            combined_parts = [title, content] + extra_fields
            combined_text = '\n'.join(part for part in combined_parts if part).strip()
            texts.append(combined_text)
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Save embeddings and documents
        vector_file = self._get_vector_file_path(source)
        documents_file = self._get_documents_file_path(source)
        
        with open(vector_file, 'wb') as f:
            pickle.dump(embeddings, f)
        
        with open(documents_file, 'wb') as f:
            pickle.dump(documents, f)
        
        print(f"Stored {len(documents)} documents for {source}")
    
    def search(self, query: str, source: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents using semantic similarity
        
        Args:
            query: Search query
            source: Source to search in (JIRA, CONFLUENCE, MINDTOUCH)
            top_k: Number of top results to return
            
        Returns:
            List of tuples (document, similarity_score)
        """
        vector_file = self._get_vector_file_path(source)
        documents_file = self._get_documents_file_path(source)
        
        # Check if vector store exists for this source
        if not os.path.exists(vector_file) or not os.path.exists(documents_file):
            print(f"No vector store found for {source}")
            return []
        
        try:
            # Load stored embeddings and documents
            with open(vector_file, 'rb') as f:
                stored_embeddings = pickle.load(f)
            
            with open(documents_file, 'rb') as f:
                stored_documents = pickle.load(f)
            
            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_embedding, stored_embeddings)[0]
            
            # Get indices sorted by similarity (descending)
            sorted_indices = np.argsort(similarities)[::-1]
            
            # Enhanced filtering and result selection
            results = []
            print(f"🔍 Top similarity scores for '{query}':")
            
            # Show more results for analysis but filter by threshold
            for i, idx in enumerate(sorted_indices[:min(top_k * 2, len(sorted_indices))]):
                similarity_score = similarities[idx]
                document = stored_documents[idx]
                title = document.get('title', 'No title')
                
                print(f"   {i+1}. {title[:60]}... - Score: {similarity_score:.4f}")
                
                # Apply threshold and collect results
                if similarity_score >= self.similarity_threshold and len(results) < top_k:
                    results.append((document, float(similarity_score)))
                elif len(results) < 2 and i < 5:  # Ensure at least 2 results from top 5 if available
                    results.append((document, float(similarity_score)))
                    print(f"      ↳ Included despite low score ({similarity_score:.4f}) for minimum results")
            
            print(f"📊 Threshold: {self.similarity_threshold}, Selected {len(results)} results")
            return results
            
        except Exception as e:
            print(f"Error during semantic search: {e}")
            return []
    
    def search_all_sources(self, query: str, top_k: int = 5) -> Dict[str, List[Tuple[Dict, float]]]:
        """
        Search across all available sources
        
        Args:
            query: Search query
            top_k: Number of top results per source
            
        Returns:
            Dictionary with source names as keys and search results as values
        """
        sources = ['JIRA', 'CONFLUENCE', 'MINDTOUCH']
        results = {}
        
        for source in sources:
            source_results = self.search(query, source, top_k)
            if source_results:
                results[source] = source_results
        
        return results
    
    def update_source_documents(self, documents: List[Dict], source: str):
        """
        Update documents for a specific source (replace existing)
        
        Args:
            documents: New list of documents
            source: Source name
        """
        self.store_documents(documents, source)
    
    def get_stored_document_count(self, source: str) -> int:
        """
        Get the number of stored documents for a source
        
        Args:
            source: Source name
            
        Returns:
            Number of stored documents
        """
        documents_file = self._get_documents_file_path(source)
        
        if not os.path.exists(documents_file):
            return 0
        
        try:
            with open(documents_file, 'rb') as f:
                documents = pickle.load(f)
            return len(documents)
        except Exception:
            return 0
    
    def clear_source_vectors(self, source: str):
        """
        Clear stored vectors and documents for a specific source
        
        Args:
            source: Source name
        """
        vector_file = self._get_vector_file_path(source)
        documents_file = self._get_documents_file_path(source)
        
        for file_path in [vector_file, documents_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        print(f"Cleared vector store for {source}")
    
    def search_documents(self, documents: List[Dict], query: str, top_k: int = 5) -> Tuple[List[Dict], List[float]]:
        """
        Search through a specific set of documents using semantic similarity
        
        Args:
            documents: List of documents to search through
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            Tuple of (ranked_documents, similarity_scores)
        """
        if not documents:
            return [], []
        
        # Extract text content for embedding
        texts = []
        for doc in documents:
            # Create comprehensive text for better matching
            text_parts = []
            
            if 'title' in doc:
                text_parts.append(f"Title: {doc['title']}")
            if 'content' in doc:
                text_parts.append(f"Content: {doc['content']}")
            if 'summary' in doc:
                text_parts.append(f"Summary: {doc['summary']}")
            if 'description' in doc:
                text_parts.append(f"Description: {doc['description']}")
                
            texts.append(' '.join(text_parts))
        
        try:
            # Generate embeddings for documents and query
            document_embeddings = self.model.encode(texts)
            query_embedding = self.model.encode([query])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_embedding, document_embeddings)[0]
            
            # Create list of (document, score) pairs
            doc_score_pairs = list(zip(documents, similarities))
            
            # Sort by similarity score (descending)
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by threshold and return top_k
            filtered_pairs = [(doc, score) for doc, score in doc_score_pairs 
                            if score >= self.similarity_threshold][:top_k]
            
            if filtered_pairs:
                ranked_docs, scores = zip(*filtered_pairs)
                return list(ranked_docs), list(scores)
            else:
                return [], []
                
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return documents[:top_k], [0.0] * min(top_k, len(documents))