import os
import sys
import uuid
import asyncio
import csv
import json

# Force Python to see the root directory (backend/) for app imports
sys.path.append(os.getcwd())

from app.services.llm.vector_store import VectorStoreService
from app.db.session import SessionLocal
from app.models.inventory import Inventory

def extract_text_from_pdf(pdf_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except ImportError:
        print("  [ERROR] pypdf is not installed. Unable to parse PDF.")
        return ""
    except Exception as e:
        print(f"  [ERROR] Error parsing PDF {pdf_path}: {e}")
        return ""

def seed_inventory_from_csv(csv_path, client_id="default"):
    db_session = SessionLocal()
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row.get('sku', '').strip()
                name = row.get('name', '').strip()
                if not sku or not name:
                    continue
                
                # Check if SKU already exists
                existing = db_session.query(Inventory).filter(
                    Inventory.sku == sku, 
                    Inventory.client_id == client_id
                ).first()
                
                price = float(row.get('price', 0.0) or 0.0)
                stock = int(row.get('stock_quantity', 0) or row.get('stock', 0) or 0)
                
                if existing:
                    existing.name = name
                    existing.description = row.get('description', '').strip()
                    existing.price = price
                    existing.stock_quantity = stock
                else:
                    item = Inventory(
                        client_id=client_id,
                        sku=sku,
                        name=name,
                        description=row.get('description', '').strip(),
                        price=price,
                        stock_quantity=stock
                    )
                    db_session.add(item)
            db_session.commit()
            print(f"  [OK] Seeded/Updated inventory from CSV: {csv_path}")
    except Exception as e:
        db_session.rollback()
        print(f"  [ERROR] Error seeding CSV inventory: {e}")
    finally:
        db_session.close()

def seed_inventory_from_json(json_path, client_id="default"):
    db_session = SessionLocal()
    try:
        with open(json_path, mode='r', encoding='utf-8') as f:
            items_data = json.load(f)
            
        if not isinstance(items_data, list):
            items_data = [items_data]
            
        for item_data in items_data:
            sku = item_data.get('sku', '').strip()
            name = item_data.get('name', '').strip()
            if not sku or not name:
                continue
                
            existing = db_session.query(Inventory).filter(
                Inventory.sku == sku, 
                Inventory.client_id == client_id
            ).first()
            
            price = float(item_data.get('price', 0.0) or 0.0)
            stock = int(item_data.get('stock_quantity', 0) or item_data.get('stock', 0) or 0)
            
            if existing:
                existing.name = name
                existing.description = item_data.get('description', '').strip()
                existing.price = price
                existing.stock_quantity = stock
            else:
                item = Inventory(
                    client_id=client_id,
                    sku=sku,
                    name=name,
                    description=item_data.get('description', '').strip(),
                    price=price,
                    stock_quantity=stock
                )
                db_session.add(item)
        db_session.commit()
        print(f"  [OK] Seeded/Updated inventory from JSON: {json_path}")
    except Exception as e:
        db_session.rollback()
        print(f"  [ERROR] Error seeding JSON inventory: {e}")
    finally:
        db_session.close()

async def master_ingestor(kb_path="./knowledge_base", client_id="default"):
    # Initialize connection to your ChromaDB
    db = VectorStoreService(client_id=client_id)

    if not os.path.exists(kb_path):
        print(f"Error: {kb_path} folder not found. Create it first!")
        return

    print(f"[START] Starting Ingestion from {kb_path}...")

    for filename in os.listdir(kb_path):
        file_path = os.path.join(kb_path, filename)
        
        # 1. Handle Inventory CSV Seeding
        if filename.endswith(".csv"):
            print(f"[INVENTORY] Processing Inventory CSV: {filename}")
            seed_inventory_from_csv(file_path, client_id=client_id)
            
        # 2. Handle Inventory JSON Seeding
        elif filename.endswith(".json") and not filename.startswith("package"):
            print(f"[INVENTORY] Processing Inventory JSON: {filename}")
            seed_inventory_from_json(file_path, client_id=client_id)
            
        # 3. Handle Knowledge Documents (.md, .txt, .pdf)
        elif filename.endswith((".md", ".txt", ".pdf")):
            print(f"[DOC] Processing Knowledge Doc: {filename}")
            
            content = ""
            if filename.endswith(".pdf"):
                content = extract_text_from_pdf(file_path)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
            if not content.strip():
                print(f"  [WARNING] Warning: Empty content in {filename}. Skipping.")
                continue

            # Split by double newlines to keep logical paragraphs together
            chunks = [c.strip() for c in content.split('\n\n') if c.strip()]

            for chunk in chunks:
                unique_id = str(uuid.uuid4())
                await db.add_memory(
                    text=chunk, 
                    metadata={
                        "source": filename, 
                        "id": unique_id,
                        "category": "business_knowledge",
                        "client_id": client_id
                    }
                )
                print(f"  [OK] Saved Chunk ({unique_id[:8]}...): {chunk[:50]}...")

    print(f"\n[DONE] Ingestion Complete for client '{client_id}'. Your Office Administrator is ready.")

if __name__ == "__main__":
    # Get parameters from arguments if any
    client = "default"
    path = "./knowledge_base"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    if len(sys.argv) > 2:
        client = sys.argv[2]
        
    asyncio.run(master_ingestor(kb_path=path, client_id=client))