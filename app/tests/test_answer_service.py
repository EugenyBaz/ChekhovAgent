import asyncio

from app.services import LLMService  # автоматически мок или реальный сервис


async def main():
    llm_service = LLMService()
    response = await llm_service.generate_response("Chekhov Sport")
    print(response)


asyncio.run(main())
