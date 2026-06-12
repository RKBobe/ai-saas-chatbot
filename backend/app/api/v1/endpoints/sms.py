from fastapi import APIRouter, Response, Form, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from app.services.agent.office_agent import OfficeAgent

router = APIRouter()

@router.post("/twilio")
async def twilio_sms_webhook(
    Body: str = Form(...),
    From: str = Form(...),
    client_id: str = "default"
):
    """
    Webhook endpoint for Twilio incoming SMS.
    Returns TwiML MessagingResponse.
    """
    try:
        sender_phone = From
        incoming_message = Body.strip()
        
        print(f"[SMS] Incoming SMS from {sender_phone}: {incoming_message}")
        
        # 1. Instantiate Office Agent for SMS channel
        # We isolate the conversation context by using the sender's phone number as the session ID
        agent = OfficeAgent(
            client_id=client_id,
            channel="sms",
            session_id=sender_phone
        )
        
        # 2. Get Response from AI agent
        reply_text = await agent.get_response(incoming_message)
        
        # 3. Format Response as Twilio TwiML
        twiml_response = MessagingResponse()
        twiml_response.message(reply_text)
        
        return Response(
            content=str(twiml_response), 
            media_type="application/xml"
        )
    except Exception as e:
        print(f"Error in Twilio SMS Webhook: {e}")
        # Return fallback TwiML so Twilio doesn't crash
        fallback_response = MessagingResponse()
        fallback_response.message("I'm sorry, our assistant is experiencing technical difficulties. Please try again later.")
        return Response(
            content=str(fallback_response), 
            media_type="application/xml"
        )
