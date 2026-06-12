from fastapi import APIRouter, HTTPException
from app.services.agent.office_agent import OfficeAgent
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

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
    Unified chat endpoint to interact with the Office Administrator agent.
    Isolates context dynamically by client_id.
    """
    try:
        # Instantiate the unified agent
        agent = OfficeAgent(
            client_id=request.client_id,
            channel="web",
            session_id=request.user_id
        )
        
        # Execute agent query
        reply_text = await agent.get_response(request.message)
        
        return {
            "reply": reply_text,
            "client_id": request.client_id,
            "user_id": request.user_id
        }
    except Exception as e:
        print(f"Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
