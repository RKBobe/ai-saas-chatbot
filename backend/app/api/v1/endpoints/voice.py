from fastapi import APIRouter, Response, Form, Request
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.services.agent.office_agent import OfficeAgent
from typing import Optional

router = APIRouter()

@router.post("/twilio")
async def twilio_voice_start(
    From: str = Form(...),
    client_id: str = "default"
):
    """
    Initial webhook triggered when a customer calls the Twilio number.
    Returns TwiML to greet and gather the first speech query.
    """
    response = VoiceResponse()
    
    # Greet user and gather speech
    gather = Gather(
        input="speech",
        action=f"/api/v1/voice/twilio/process?client_id={client_id}",
        method="POST",
        speechTimeout="auto",
        enhanced=True
    )
    gather.say("Hello! Welcome to our office assistant. How can I help you today?")
    response.append(gather)
    
    # Fallback if user doesn't say anything
    response.say("I didn't hear anything. Thank you for calling. Goodbye!")
    
    return Response(
        content=str(response),
        media_type="application/xml"
    )

@router.post("/twilio/process")
async def twilio_voice_process(
    From: str = Form(...),
    SpeechResult: Optional[str] = Form(None),
    client_id: str = "default"
):
    """
    Processes the user's speech transcript via the OfficeAgent and speaks back the response.
    Keeps the conversation going in a gather loop.
    """
    response = VoiceResponse()
    
    # If we didn't receive a speech transcript, ask the user again
    if not SpeechResult or not SpeechResult.strip():
        gather = Gather(
            input="speech",
            action=f"/api/v1/voice/twilio/process?client_id={client_id}",
            method="POST",
            speechTimeout="auto"
        )
        gather.say("I'm sorry, I didn't catch that. Could you please repeat it?")
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
        
    user_speech = SpeechResult.strip()
    print(f"[VOICE] Voice Call speech from {From}: {user_speech}")
    
    try:
        # 1. Instantiate Office Agent for Voice channel
        agent = OfficeAgent(
            client_id=client_id,
            channel="voice",
            session_id=From
        )
        
        # 2. Get response from AI Agent
        reply_text = await agent.get_response(user_speech)
        
        # 3. Speak the response and Gather the next question
        gather = Gather(
            input="speech",
            action=f"/api/v1/voice/twilio/process?client_id={client_id}",
            method="POST",
            speechTimeout="auto"
        )
        # Twilio's Speak response
        gather.say(reply_text)
        response.append(gather)
        
        # Fallback if they stay silent
        response.say("Thank you for calling. Goodbye!")
        
    except Exception as e:
        print(f"Error in Voice processing: {e}")
        response.say("I'm sorry, I encountered an internal error. Please call back later.")
        
    return Response(
        content=str(response),
        media_type="application/xml"
    )
