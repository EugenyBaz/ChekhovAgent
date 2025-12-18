import logging

from aiogram import Router, types
from aiogram.filters import CommandStart

from app.config import settings
from app.services.answer_service import LLMService
from app.services.answer_service_mock import LLMServiceMock

logger = logging.getLogger(__name__)

router = Router()
if settings.USE_MOCK_LLM:
    llm_service = LLMServiceMock()
else:
    llm_service = LLMService()


# ------------------- Обработчик /start -------------------
@router.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    """
    Приветствие пользователя при /start.
    Инициализация состояния пользователя в LLMService.
    """
    user_id = message.from_user.id

    # Инициализация state пользователя
    if user_id not in llm_service.user_states:
        llm_service.user_states[user_id] = {
            "state": "NEED_CLUB",
            "club": None,
            "time_preference": None,
        }

    await message.answer(
        "Привет! 👋 Я Малика, ваш помощник по фитнес-клубам Chekhov Sport Club.\n"
        "Напишите район, город или название конкретного клуба, и я помогу подобрать абонемент."
    )


# ------------------- Обработчик текста -------------------
@router.message()
async def text_handler(message: types.Message) -> None:
    """
    Обрабатывает текстовые сообщения пользователя и возвращает ответ
    через LLMService, учитывая state и intent.
    """
    user_id = message.from_user.id
    user_text = message.text.strip()

    logger.info("User %s query: %s", user_id, user_text)

    try:
        # Генерация ответа с учетом состояния пользователя
        response = await llm_service.generate_response(user_id, user_text)
        await message.answer(response)

    except Exception as e:
        logger.exception("Ошибка при обработке сообщения пользователя: %s", e)
        await message.answer(
            "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."
        )
