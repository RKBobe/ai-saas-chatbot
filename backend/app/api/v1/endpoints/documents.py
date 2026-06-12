import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from app.core.config import settings
from ingest import master_ingestor

router = APIRouter()
KB_DIR = "./knowledge_base"

# Ensure the upload directory exists
os.makedirs(KB_DIR, exist_ok=True)

async def run_ingestion_background(client_id: str):
    try:
        await master_ingestor(kb_path=KB_DIR, client_id=client_id)
    except Exception as e:
        print(f"Error running ingestion in background: {e}")

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: str = "default"
):
    if not file.filename.endswith(('.md', '.txt', '.pdf')):
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Only .md, .txt, and .pdf are allowed."
        )
        
    try:
        # Save file to knowledge base directory
        file_path = os.path.join(KB_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Trigger ingestion in the background
        background_tasks.add_task(run_ingestion_background, client_id)
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' uploaded successfully. Ingestion started in background."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

@router.get("/", response_model=List[str])
def list_documents():
    try:
        if not os.path.exists(KB_DIR):
            return []
        return [f for f in os.listdir(KB_DIR) if os.path.isfile(os.path.join(KB_DIR, f)) and f.endswith(('.md', '.txt', '.pdf'))]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")

@router.delete("/{filename}")
def delete_document(filename: str):
    file_path = os.path.join(KB_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        os.remove(file_path)
        # Note: In a production system, we would also remove the vectors from ChromaDB.
        # But for this version, deleting the file prevents re-ingestion, and the vector store remains queryable.
        return {"status": "success", "message": f"File '{filename}' deleted from knowledge base."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")
