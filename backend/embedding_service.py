"""
Embedding Service
Converts text chunks to 384-dimensional vectors using all-MiniLM-L6-v2
"""

from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        """Load the embedding model (runs once when backend starts)"""
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded (384 dimensions)")
    
    def embed_text(self, text: str) -> list:
        """
        Convert single text to embedding
        
        Args:
            text: Text to embed
            
        Returns: List of 384 floats (one vector)
        """
        embedding = self.model.encode(text)
        return embedding.tolist()  # Convert to list for JSON
    
    def embed_batch(self, texts: list) -> list:
        """
        Convert multiple texts to embeddings (faster than one-by-one)
        
        Args:
            texts: List of text strings
            
        Returns: List of embeddings (each is 384 floats)
        """
        embeddings = self.model.encode(texts)
        return [e.tolist() for e in embeddings]

# Global instance - loads once when backend starts
embedding_service = EmbeddingService()