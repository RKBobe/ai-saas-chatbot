import httpx
import logging

logger = logging.getLogger(__name__)

class FacebookService:
    BASE_URL = "https://graph.facebook.com/v19.0/me/messages"

    @staticmethod
    async def send_message(token: str, recipient_id: str, message_text: str):
        """
        Sends a plain text message to a Facebook user via the Graph API.
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "access_token": token
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                FacebookService.BASE_URL, 
                json=payload, 
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Facebook API Error: {response.text}")
                # Optional: Raise exception if you want to retry