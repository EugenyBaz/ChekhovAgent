import logging

from openai import OpenAI

from app.clients.google_sheets import sheets_client
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM сервис на базе DeepSeek"""

    def __init__(self):
        # Инициализация клиента DeepSeek через OpenAI SDK
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,  # обычно https://api.deepseek.com
        )

    async def generate_response(self, query: str) -> str:
        """
        Берём запрос пользователя, ищем данные в Google Sheets и формируем текст через DeepSeek
        """
        # Получаем данные из Google Sheets
        department = await sheets_client.find_department(query)

        if not department:
            return "Не нашёл такую запись в таблице. Попробуйте уточнить запрос."

        # Формируем "промпт" для LLM
        prompt = (
            f"Пользователь спрашивает о {query}. Вот данные из таблицы:\n"
            f"Название: {department.get('Name')}\n"
            f"Телефон: {department.get('phone')}\n"
            f"Адрес: {department.get('address')}\n"
            f"Заметки: {department.get('Notes')}\n\n"
            f"Составь короткий, понятный и дружелюбный ответ для пользователя."
        )

        try:
            # Вызываем DeepSeek через OpenAI SDK
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            answer = response.choices[0].message.content.strip()
            logger.info("Ответ от DeepSeek успешно получен")
            return answer

        except Exception:
            logger.exception("Ошибка при обращении к DeepSeek API")
            return "Ошибка при формировании ответа. Попробуйте позже."
