from langchain_openai import ChatOpenAI
# FIX: Import from langchain_core.messages instead of langchain.schema
from langchain_core.messages import SystemMessage, HumanMessage 
from app.core.config import settings

class RAGService:
    @staticmethod
    async def generate_response(user_query: str, context: str, system_prompt: str) -> str:
        """
        Combines the System Prompt + Context + User Query.
        """
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY, 
            model="gpt-4-turbo-preview", 
            temperature=0.7
        )

        messages = [
            SystemMessage(content=f"{system_prompt}\n\nRelevant Context from Knowledge Base:\n{context}"),
            HumanMessage(content=user_query)
        ]

        response = await llm.ainvoke(messages)
        return response.content