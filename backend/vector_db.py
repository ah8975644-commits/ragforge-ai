"""
Vector Database Service
Stores and retrieves embeddings from Supabase pgvector
"""

import os
from supabase import create_client, Client
from typing import List, Dict
import math

class VectorDB:
    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase pgvector")
    
    def store_chunks(self, doc_id: str, filename: str, chunks: List[str], 
                    embeddings: List[List[float]]) -> int:
        """
        Store chunk embeddings in Supabase
        
        Args:
            doc_id: Unique document ID
            filename: Original PDF filename
            chunks: List of text chunks
            embeddings: List of 384-dimensional vectors
            
        Returns: Number of chunks successfully stored
        """
        stored_count = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:

                # DEBUG: Check embedding type and format
                print(type(embedding))
                print(str(embedding)[:200])

                self.client.table("documents").insert({
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "embedding": embedding  # Store as vector
                }).execute()
                stored_count += 1
            except Exception as e:
                print(f"❌ Error storing chunk {i}: {str(e)}")
        
        print(f"✅ Stored {stored_count}/{len(chunks)} chunks in Supabase")
        return stored_count
    
    def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """
        Find similar chunks using vector similarity (cosine distance)
        
        Args:
            query_embedding: 384-dimensional query vector
            limit: Number of top results to return
            
        Returns: List of similar chunks with metadata
        """
        try:
            # Fetch all documents with embeddings
            response = self.client.table("documents").select(
                "id, doc_id, filename, chunk_index, chunk_text, embedding"
            ).execute()
            
            if not response.data:
                print("⚠️ No documents in database")
                return []
            
            # Calculate cosine similarity for each chunk
            def cosine_similarity(vec_a: list, vec_b: list) -> float:
                """Calculate cosine similarity between two vectors"""
                dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
                norm_a = math.sqrt(sum(x * x for x in vec_a))
                norm_b = math.sqrt(sum(x * x for x in vec_b))
                
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                
                return dot_product / (norm_a * norm_b)
            
            # Score all chunks
            scored_chunks = []
            for chunk in response.data:
                similarity_score = cosine_similarity(
                    query_embedding, 
                    chunk['embedding']
                )
                
                scored_chunks.append({
                    "filename": chunk['filename'],
                    "chunk_index": chunk['chunk_index'],
                    "chunk_text": chunk['chunk_text'],
                    "similarity": similarity_score
                })
            
            # Sort by similarity (highest first) and return top N
            top_results = sorted(
                scored_chunks, 
                key=lambda x: x['similarity'],
                reverse=True
            )[:limit]
            
            return top_results
            
        except Exception as e:
            print(f"❌ Error searching similar chunks: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete all chunks for a document
        
        Args:
            doc_id: Document ID to delete
            
        Returns: True if successful
        """
        try:
            self.client.table("documents").delete().eq("doc_id", doc_id).execute()
            print(f"✅ Deleted all chunks for {doc_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting document: {str(e)}")
            return False
    
    def get_document_count(self) -> int:
        """Get total number of stored chunks"""
        try:
            response = self.client.table("documents").select(
                "id", 
                count="exact"
            ).execute()
            return response.count if response.count else 0
        except:
            return 0

# Global instance - connects once when backend starts
vector_db = VectorDB()