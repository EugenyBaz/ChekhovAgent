import logging
from app.clients.google_sheets import sheets_client

logger = logging.getLogger(__name__)

class LLMServiceMock:
    """Мок LLM-сервиса для тестирования без реального API"""

    async def generate_response(self, query: str) -> str:
        # Получаем данные из Google Sheets (можно оставить реальное чтение)
        department = await sheets_client.find_department(query)

        if not department:
            return "Не нашёл такую запись в таблице. Попробуйте уточнить запрос."

        # Возвращаем статический или сгенерированный ответ
        logger.info(f"[MOCK] формируем ответ для {query}")
        return (
            f"[MOCK] Информация о {department.get('Name')}:\n"
            f"Адрес: {department.get('address')}\n"
            f"Телефон: {department.get('phone')}\n"
            f"Примечания: {department.get('Notes')}"
        )