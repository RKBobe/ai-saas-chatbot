from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from app.core.config import settings
from app.services.social.facebook import FacebookService
from app.services.llm.rag_chain import RAGService # We will build this next
import logging
from app.models.chatbot import Chatbot
from app.services.llm.vector_store import VectorStoreService
from app.db.session import SessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)

# 1. Verification Step (Facebook calls this when you first set up the webhook)
@router.get("/facebook")
async def verify_fb_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    return {"status": "ok"}

# 2. Event Listener (Facebook sends messages here)
@router.post("/facebook")
async def fb_webhook_listener(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # Extract the event
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            # The Page ID the message was sent to (Use this to find the Tenant!)
            page_id = entry.get("id") 
            
            for event in entry.get("messaging", []):
                if event.get("message"):
                    sender_id = event["sender"]["id"]
                    message_text = event["message"].get("text")
                    
                    if message_text:
                        # Offload the heavy AI processing to background
                        background_tasks.add_task(
                            process_incoming_message, 
                            page_id, 
                            sender_id, 
                            message_text
                        )
        return {"status": "received"}
    
    raise HTTPException(status_code=404, detail="Event not supported")

# 3. The Background Processor
async def process_incoming_message(page_id: str, sender_id: str, text: str):
    """
    1. Look up which Tenant owns this 'page_id'
    2. Get their specific System Prompt and Vector Data
    3. Generate AI Response
    4. Send back via Facebook Graph API
    """
    try:
        # 1. Start a temporary DB session (Background Tasks dont share the request context)
        db = SessionLocal()
        bot = db.query(Chatbot).filter(Chatbot.fb_page_id == page_id).first()
        
        if not bot:
            print(f"Warning: Received message for unknown page ID: {page_id}")
            return
        if not bot.is_active:
            print(f"Bot {bot.name} (ID: {bot.id}) is currently inactive.")
            return
        # ---- Retrieve Context (RAG) ----
        # We use the bots unique database ID as the 'client_id' to ensure data isolation
        #this prevents cross-tenant data leaks
        context_chunks = VectorStoreService.query_documents(
            client_id=str(bot.id),
            query=text
        )
        
        #Flatten the list of chunks into a single string
        context_str = "\n\n".join(context_chunks) if context_chunks else ""
        
        # --- STEP C: GENERATE AI RESPONSE ---
        # We pass the specific System Prompt the user configured in their dashboard.
        ai_reply = await RAGService.generate_response(
            user_query=text,
            context=context_str,
            system_prompt=bot.system_prompt
        )

        # --- STEP D: SEND TO FACEBOOK ---
        # Use the specific Page Access Token for this bot
        await FacebookService.send_message(
            token=bot.fb_page_access_token,
            recipient_id=sender_id,
            message_text=ai_reply
        )
            
        print(f"Success: Replied to user {sender_id} on behalf of bot {bot.id}")

    except Exception as e:
        print(f"CRITICAL ERROR in process_incoming_message: {e}")
        # In a real app, you would log this to Sentry or Datadog
            
    finally:
        db.close() # distinct session must be closed manually
    
    
   