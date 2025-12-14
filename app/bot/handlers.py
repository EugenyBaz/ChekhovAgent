import logging

from aiogram import Router, types
from aiogram.filters import CommandStart

from app.services import LLMService

logger = logging.getLogger(__name__)

router = Router()
llm_service = LLMService()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Напиши название отдела или организации, и я постараюсь найти информацию."
    )


@router.message()
async def text_handler(message: types.Message):
    user_text = message.text.strip()

    logger.info("User query: %s", user_text)

    response = await llm_service.generate_response(user_text)

    await message.answer(response)