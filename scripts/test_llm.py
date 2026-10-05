import asyncio
from app.config import get_settings
from app.services.llm import LLMService
import traceback

async def main():
    settings = get_settings()
    llm = LLMService(settings)
    
    print("Testing LLM...")
    try:
        res = await llm.classify_intent("I want a refund")
        print("Success:", res)
    except Exception as e:
        print("Exception occurred!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
