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
    
    def _prepare_document_text(self, doc: Dict) -> str:
        """
        Extract and combine text fields from document for embedding
        
        Args:
            doc: Document dictionary with various text fields
            
        Returns:
            Combined text string ready for embedding
        """
        text_parts = []
        
        # Primary content fields
        title = doc.get('title', '')
        if title:
            text_parts.append(f"Title: {title}")
            
        # Content field with fallbacks
        content = doc.get('content', '') or doc.get('summary', '') or doc.get('description', '')
        if content:
            text_parts.append(f"Content: {content}")
        
        # Additional specific fields that might exist
        if doc.get('summary') and doc.get('summary') != content:
            text_parts.append(f"Summary: {doc.get('summary')}")
        if doc.get('description') and doc.get('description') != content:
            text_parts.append(f"Description: {doc.get('description')}")
        
        # Metadata fields for enhanced context
        if doc.get('labels'):
            labels = doc.get('labels', [])
            if isinstance(labels, list):
                text_parts.append(f"Labels: {', '.join(labels)}")
            else:
                text_parts.append(f"Labels: {labels}")
        
        if doc.get('status'):
            text_parts.append(f"Status: {doc.get('status')}")
            
        if doc.get('priority'):
            text_parts.append(f"Priority: {doc.get('priority')}")
        
        # Combine all parts
        combined_text = '\n'.join(text_parts).strip()
        return combined_text if combined_text else doc.get('title', 'No content')
    
    def _calculate_similarities(self, query: str, documents: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Calculate cosine similarities between query and documents
        
        Args:
            query: Search query
            documents: List of documents to compare against
            
        Returns:
            List of (document, similarity_score) tuples sorted by score descending
        """
        if not documents:
            return []
        
        try:
            # Extract text content for embedding
            texts = [self._prepare_document_text(doc) for doc in documents]
            
            # Generate embeddings for documents and query
            document_embeddings = self.model.encode(texts)
            query_embedding = self.model.encode([query])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_embedding, document_embeddings)[0]
            
            # Create list of (document, score) pairs
            doc_score_pairs = list(zip(documents, similarities))
            
            # Sort by similarity score (descending)
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return doc_score_pairs
            
        except Exception as e:
            print(f"Error calculating similarities: {e}")
            return [(doc, 0.0) for doc in documents]
    
    def _filter_by_threshold(self, doc_score_pairs: List[Tuple[Dict, float]], top_k: int) -> List[Tuple[Dict, float]]:
        """
        Apply similarity threshold filtering with fallback logic
        
        Args:
            doc_score_pairs: List of (document, score) tuples sorted by score
            top_k: Maximum number of results to return
            
        Returns:
            Filtered list of (document, score) tuples
        """
        results = []
        
        for i, (doc, score) in enumerate(doc_score_pairs[:top_k * 2]):  # Check more results than needed
            # Apply threshold and collect results
            if score >= self.similarity_threshold and len(results) < top_k:
                results.append((doc, float(score)))
            elif len(results) < 2 and i < 5:  # Ensure at least 2 results from top 5 if available
                results.append((doc, float(score)))
                if hasattr(self, '_debug_mode'):  # Optional debug logging
                    print(f"      ↳ Included despite low score ({score:.4f}) for minimum results")
        
        return results[:top_k]
    
    def store_documents(self, documents: List[Dict], source: str):
        """
        Store documents and their embeddings for a specific source
        
        Args:
            documents: List of documents with 'content', 'title', and other metadata
            source: Source name (JIRA, CONFLUENCE, MINDTOUCH)
        """
        if not documents:
            return
        
        # Extract text content for embedding using unified method
        texts = [self._prepare_document_text(doc) for doc in documents]
        
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
            
            # Create document-score pairs and apply filtering
            doc_score_pairs = [(stored_documents[idx], similarities[idx]) 
                             for idx in sorted_indices]
            
            # Show top results for analysis
            for i, (document, similarity_score) in enumerate(doc_score_pairs[:min(top_k * 2, len(doc_score_pairs))]):
                title = document.get('title', 'No title')
                print(f"   {i+1}. {title[:60]}... - Score: {similarity_score:.4f}")
            
            # Apply threshold filtering
            results = self._filter_by_threshold(doc_score_pairs, top_k)
            
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
    
    def search_documents(self, documents: List[Dict], query: str, top_k: int = 5, learning_manager=None) -> Tuple[List[Dict], List[float]]:
        """
        Search through a specific set of documents using semantic similarity with adaptive learning
        
        Args:
            documents: List of documents to search through
            query: Search query
            top_k: Number of top results to return
            learning_manager: Optional learning manager for adaptive parameters
            
        Returns:
            Tuple of (ranked_documents, similarity_scores)
        """
        if not documents:
            return [], []
        
        try:
            # 🧠 Get adaptive parameters from learning manager if available
            adaptive_threshold = self.similarity_threshold
            if learning_manager:
                try:
                    adaptive_params = learning_manager.get_adaptive_search_parameters()
                    adaptive_threshold = adaptive_params.get('similarity_threshold', self.similarity_threshold)
                    print(f"🎯 Using adaptive similarity threshold: {adaptive_threshold}")
                except Exception as e:
                    print(f"⚠️ Learning parameters unavailable, using defaults: {e}")
            
            # Calculate similarities using unified method
            doc_score_pairs = self._calculate_similarities(query, documents)
            
            # 🧠 Apply adaptive threshold instead of fixed threshold
            filtered_pairs = [(doc, score) for doc, score in doc_score_pairs 
                            if score >= adaptive_threshold][:top_k]
            
            # Fallback to ensure minimum results if adaptive threshold too strict
            if not filtered_pairs and doc_score_pairs:
                print(f"🔄 Adaptive threshold too strict, falling back to top results")
                filtered_pairs = doc_score_pairs[:min(2, top_k)]
            
            if filtered_pairs:
                ranked_docs, scores = zip(*filtered_pairs)
                return list(ranked_docs), list(scores)
            else:
                return [], []
                
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return documents[:top_k], [0.0] * min(top_k, len(documents))