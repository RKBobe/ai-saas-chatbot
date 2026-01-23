import httpx
from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from app.core.config import settings
from app.services.llm.vector_store import VectorStoreService
from app.services.llm.gemini_service import GeminiService

router = APIRouter()

# --- Initialize Services ---
vector_service = VectorStoreService()
llm_service = GeminiService()  

print("✅ GEMINI BRAIN LOADED")

# --- 1. THE SPEAKER ---
async def send_fb_message(recipient_id: str, text: str):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={settings.FB_PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

# --- 2. THE HANDSHAKE ---
@router.get("/facebook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

# --- 3. THE BRAIN ---
@router.post("/facebook")
async def facebook_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        entry = data['entry'][0]
        messaging_events = entry.get('messaging', [])
        
        for event in messaging_events:
            if 'message' in event and 'text' in event['message']:
                sender_id = event['sender']['id']
                user_text = event['message']['text']
                print(f"User said: {user_text}")

                # Mode A: TEACHING
                if user_text.lower().startswith("learn:"):
                    new_fact = user_text[6:].strip()
                    await vector_service.add_memory(new_fact, {"source": "facebook"})
                    reply_text = "✅ I have filed that information away."

                # Mode B: THINKING (RAG Pipeline)
                else:
                    # 1. Search Memory
                    results = await vector_service.search(user_text)
                    documents = results.get('documents', [])
                    
                    if documents and documents[0]:
                        found_memory = documents[0][0] # The raw fact
                        
                        # 2. Ask OpenAI to synthesize the answer
                        print(f"Found context: {found_memory}")
                        reply_text = await llm_service.generate_response(user_text, found_memory)
                    else:
                        reply_text = "I searched my database, but I don't know the answer to that yet."
                
                # Send the final AI answer
                background_tasks.add_task(send_fb_message, sender_id, reply_text)

        return {"status": "ok"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error"}