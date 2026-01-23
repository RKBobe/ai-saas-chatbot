import google.generativeai as genai
from app.core.config import settings

# Configure the API with your key
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    async def generate_response(self, user_query: str, context: str):
        """
        Uses Google Gemini to answer the question based on the context.
        """
        prompt = f"""
        You are a helpful AI assistant for a SaaS platform.
        
        Context Information (Facts you know):
        {context}
        
        User Question:
        {user_query}
        
        Instructions:
        Answer the user's question using ONLY the Context Information above.
        If the answer is not in the context, say "I don't have that information yet."
        Be polite and professional.
        """
        
        try:
            # Use the standard Gemini Pro model
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Generate response (Async)
            response = await model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return "I'm having trouble thinking right now. Please try again later."