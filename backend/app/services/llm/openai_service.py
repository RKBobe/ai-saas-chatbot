from openai import AsyncOpenAI
from app.core.config import settings

# Initialize the new Client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class LLMService:
    async def generate_response(self, user_query: str, context: str):
        """
        Sends the user's question + the memory we found to OpenAI
        and asks it to write a nice answer.
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
            # Updated syntax for OpenAI v1.0+
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            # Updated way to access the answer
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return "I'm having trouble thinking right now. Please try again later."