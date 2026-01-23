import chromadb
from app.core.config import settings

# --- FIX: Connect to Docker on Localhost Port 8001 ---
# We explicitly tell it: Host is "localhost", Port is 8001
chroma_client = chromadb.HttpClient(host="localhost", port=8001)

class VectorStoreService:
    def __init__(self):
        # We use the client created above
        self.client = chroma_client
        # Get or create the collection for our pirate memories
        self.collection = self.client.get_or_create_collection(name="pirate_memories")

    async def search(self, query: str):
        # Simple placeholder search
        results = self.collection.query(
            query_texts=[query],
            n_results=1
        )
        return results

    async def add_memory(self, text: str, metadata: dict):
        # Simple placeholder to add memory
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(metadata.get("id", "temp_id"))]
        )