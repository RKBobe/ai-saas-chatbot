from fastapi import APIRouter, HTTPException, Body
from app.services.llm.vector_store import VectorStoreService
from app.services.llm.gemini_service import GeminiService
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
llm_service = GeminiService()

class ChatRequest(BaseModel):
    message: str
    client_id: str = "default"
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    reply: str
    client_id: str
    user_id: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Generic chat endpoint to interact with client-specific knowledge bases.
    """
    try:
        # 1. Initialize Vector Store for this specific client
        vector_service = VectorStoreService(client_id=request.client_id)
        
        # 2. Search client-specific knowledge base
        results = await vector_service.search(request.message)
        documents = results.get('documents', [])
        
        context = ""
        if documents and documents[0]:
            # Flatten context from multiple results
            context = "\n".join(documents[0])
            
        # 3. Generate response using Gemini
        # Multi-tenant context is automatically isolated via VectorStoreService
        reply_text = await llm_service.generate_response(request.message, context)
        
        return {
            "reply": reply_text,
            "client_id": request.client_id,
            "user_id": request.user_id
        }
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
