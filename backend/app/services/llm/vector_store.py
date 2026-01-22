import chromadb
from app.core.config import settings

# Initialize Chroma Client
chroma_client = chromadb.HttpClient(host=settings.CHROMA_DB_URL)
collection = chroma_client.get_or_create_collection(name="saas_knowledge_base")

class VectorStoreService:
    
    @staticmethod
    def add_documents(client_id: str, chunks: list[str], metadatas: list[dict]):
        """
        Adds documents to the vector store with forced client_id metadata.
        """
        # Inject client_id into every single metadata dict
        secure_metadatas = []
        for meta in metadatas:
            meta["client_id"] = str(client_id) # FORCE the client ID
            secure_metadatas.append(meta)

        # Create IDs for chunks (or let Chroma do it)
        ids = [f"{client_id}_{i}" for i in range(len(chunks))]

        collection.add(
            documents=chunks,
            metadatas=secure_metadatas,
            ids=ids
        )

    @staticmethod
    def query_documents(client_id: str, query: str, n_results: int = 3):
        """
        Queries the vector store ONLY for documents belonging to client_id.
        """
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            # THE SAFETY LOCK: This filter prevents data leaks between tenants
            where={"client_id": str(client_id)} 
        )
        return results['documents'][0]