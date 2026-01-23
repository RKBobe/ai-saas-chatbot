import httpx
from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from app.core.config import settings

router = APIRouter()

# --- DEBUG: Print this when the file loads ---
print("✅ NEW WEBHOOKS CODE LOADED SUCCESSFULLY")

async def send_fb_message(recipient_id: str, text: str):
    print(f"Attempting to reply to {recipient_id}...") 
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={settings.FB_PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            print(">> Reply sent successfully!")
        else:
            print(f"!! Error sending message: {response.text}")

@router.get("/facebook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

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
                
                # Reply back
                reply_text = f"You said: {user_text}"
                background_tasks.add_task(send_fb_message, sender_id, reply_text)

        return {"status": "ok"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error"}