import chromadb
from app.core.config import settings
import uuid
from typing import Optional

# --- Singleton Client Pattern ---
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST, 
            port=settings.CHROMA_PORT
        )
    return _chroma_client

class VectorStoreService:
    def __init__(self, client_id: str = "default"):
        self.client = get_chroma_client()
        # Each client gets their own isolated collection
        self.collection_name = f"client_{client_id}_memories"
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    async def search(self, query: str, n_results: int = 3):
        # Search client-specific knowledge base
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    async def add_memory(self, text: str, metadata: dict = None):
        if metadata is None:
            metadata = {}
        # Generate a unique ID for the memory
        unique_id = str(metadata.get("id", uuid.uuid4()))
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[unique_id]
        )
