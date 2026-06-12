import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import SessionLocal
from app.models.inventory import Inventory

router = APIRouter()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class InventoryItemBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float = 0.0
    stock_quantity: int = 0

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int
    client_id: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[InventoryItemResponse])
def get_inventory(
    client_id: str = "default",
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    db_query = db.query(Inventory).filter(Inventory.client_id == client_id)
    if query:
        search_pattern = f"%{query}%"
        db_query = db_query.filter(
            (Inventory.sku.ilike(search_pattern)) | 
            (Inventory.name.ilike(search_pattern))
        )
    return db_query.all()

@router.post("/", response_model=InventoryItemResponse)
def create_or_update_item(
    item: InventoryItemCreate,
    client_id: str = "default",
    db: Session = Depends(get_db)
):
    # Check if exists
    db_item = db.query(Inventory).filter(
        Inventory.client_id == client_id,
        Inventory.sku == item.sku
    ).first()
    
    if db_item:
        db_item.name = item.name
        db_item.description = item.description
        db_item.price = item.price
        db_item.stock_quantity = item.stock_quantity
    else:
        db_item = Inventory(
            client_id=client_id,
            sku=item.sku,
            name=item.name,
            description=item.description,
            price=item.price,
            stock_quantity=item.stock_quantity
        )
        db.add(db_item)
        
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    client_id: str = "default",
    db: Session = Depends(get_db)
):
    db_item = db.query(Inventory).filter(
        Inventory.id == item_id,
        Inventory.client_id == client_id
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"status": "success", "message": f"Item {item_id} deleted."}

@router.post("/upload-csv")
async def upload_inventory_csv(
    file: UploadFile = File(...),
    client_id: str = "default",
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        reader = csv.DictReader(StringIO(csv_data))
        
        items_count = 0
        for row in reader:
            sku = row.get('sku', '').strip()
            name = row.get('name', '').strip()
            if not sku or not name:
                continue
                
            db_item = db.query(Inventory).filter(
                Inventory.client_id == client_id,
                Inventory.sku == sku
            ).first()
            
            price = float(row.get('price', 0.0) or 0.0)
            stock = int(row.get('stock_quantity', 0) or row.get('stock', 0) or 0)
            
            if db_item:
                db_item.name = name
                db_item.description = row.get('description', '').strip()
                db_item.price = price
                db_item.stock_quantity = stock
            else:
                db_item = Inventory(
                    client_id=client_id,
                    sku=sku,
                    name=name,
                    description=row.get('description', '').strip(),
                    price=price,
                    stock_quantity=stock
                )
                db.add(db_item)
            items_count += 1
            
        db.commit()
        return {"status": "success", "message": f"Successfully imported/updated {items_count} items."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {e}")
