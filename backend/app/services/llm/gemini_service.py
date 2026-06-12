import google.generativeai as genai
from app.core.config import settings
from typing import Optional

# Configure the API with your key
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self, default_system_prompt: str = None):
        self.default_system_prompt = default_system_prompt or (
            "You are a helpful AI assistant for a SaaS platform.\n"
            "Answer the user's question using ONLY the Context Information provided.\n"
            "If the answer is not in the context, say 'I don't have that information yet.'\n"
            "Be polite and professional."
        )

    async def generate_response(
        self, 
        user_query: str, 
        context: str, 
        system_prompt: Optional[str] = None
    ):
        """
        Uses Google Gemini to answer the question based on the context.
        """
        active_prompt = system_prompt or self.default_system_prompt
        
        full_prompt = f"""
        {active_prompt}
        
        Context Information (Facts you know):
        {context}
        
        User Question:
        {user_query}
        """
        
        try:
            # Use the latest Gemini 3.5 Flash model
            model = genai.GenerativeModel('gemini-3.5-flash')
            
            # Generate response (Async)
            response = await model.generate_content_async(full_prompt)
            return response.text
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return "I'm having trouble thinking right now. Please try again later."
