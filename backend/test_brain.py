import asyncio
import sys
import os

# 1. Force Python to see the 'app' folder
sys.path.append(os.getcwd())

from app.services.llm.vector_store import VectorStoreService
from app.services.llm.gemini_service import GeminiService

async def chat_loop():
    print("\n🧠 GEMINI BRAIN ACTIVATED (Terminal Mode)")
    print("-----------------------------------------")
    print("Type 'exit' to quit.\n")

    try:
        # Initialize Services
        vector_service = VectorStoreService()
        llm_service = GeminiService()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not start services.\n{e}")
        return

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        # --- MODE A: TEACH ---
        if user_input.lower().startswith("learn:"):
            fact = user_input[6:].strip()
            await vector_service.add_memory(fact, {"source": "terminal"})
            print(f"🤖 Bot: Memory saved! I now know '{fact}'\n")
            continue

        # --- MODE B: ASK ---
        print("... thinking ...")
        try:
            results = await vector_service.search(user_input)
            documents = results.get('documents', [])
            
            if documents and documents[0]:
                found_memory = documents[0][0]
                print(f"   (Found context: {found_memory})")
                response = await llm_service.generate_response(user_input, found_memory)
                print(f"🤖 Bot: {response}\n")
            else:
                print("🤖 Bot: I don't know that yet. Teach me using 'Learn: ...'\n")
        except Exception as e:
            print(f"❌ ERROR: {e}\n")

if __name__ == "__main__":
    # Windows-specific fix for asyncio loops
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(chat_loop())