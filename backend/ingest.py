import os
import uuid
import asyncio
from app.services.llm.vector_store import VectorStoreService  # Ensure this matches your project structure

async def master_ingestor():
    # Initialize connection to your Dockerized ChromaDB
    db = VectorStoreService()
    kb_path = "./knowledge_base"

    if not os.path.exists(kb_path):
        print(f"Error: {kb_path} folder not found. Create it first!")
        return

    print(f"🚀 Starting Ingestion from {kb_path}...")

    for filename in os.listdir(kb_path):
        if filename.endswith(".md"):
            print(f"📄 Processing: {filename}")
            
            with open(os.path.join(kb_path, filename), "r", encoding="utf-8") as f:
                content = f.read()

            # Strategy: Split by double newlines to keep logical paragraphs together
            chunks = [c.strip() for c in content.split('\n\n') if c.strip()]

            for chunk in chunks:
                # Generate a unique ID to prevent database collisions
                unique_id = str(uuid.uuid4())
                
                # Push to ChromaDB
                await db.add_memory(
                    text=chunk, 
                    metadata={
                        "source": filename, 
                        "id": unique_id,
                        "category": "commercial_logic"
                    }
                )
                print(f"  ✅ Saved Chunk ({unique_id[:8]}...): {chunk[:50]}...")

    print("\n✨ Ingestion Complete. Your bot is now an expert on itself and Treelight Innovations.")

if __name__ == "__main__":
    asyncio.run(master_ingestor())