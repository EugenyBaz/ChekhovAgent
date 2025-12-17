import logging
from enum import Enum
from typing import Optional, List

from app.clients.google_sheets import sheets_client
from app.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# ------------------- Состояния диалога -------------------
class DialogState(str, Enum):
    NEED_CLUB = "NEED_CLUB"
    NEED_TIME = "NEED_TIME"
    PRICING = "PRICING"
    CLOSING = "CLOSING"

# ------------------- Сервис LLM -------------------
class LLMService:
    """Сервис для обработки запросов пользователя и генерации ответов с контекстом диалога"""

    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        # Хранение состояния пользователей и истории сообщений
        self.user_states = {}

    # ------------------- Добавление сообщения в историю -------------------
    def add_to_history(self, user_id: int, role: str, content: str):
        history: List[dict] = self.user_states.setdefault(user_id, {}).setdefault("history", [])
        history.append({"role": role, "content": content})
        # Ограничиваем историю последними 6 сообщениями
        if len(history) > 6:
            history.pop(0)

    # ------------------- Генерация ответа -------------------
    async def generate_response(self, user_id: int, user_text: str) -> str:
        # Инициализация state пользователя
        state_data = self.user_states.setdefault(user_id, {
            "state": DialogState.NEED_CLUB,
            "club": None,
            "time_preference": None,
            "greeted": False,
            "history": []
        })

        # ------------------- Сохраняем пользовательское сообщение -------------------
        self.add_to_history(user_id, "user", user_text)

        # ------------------- Получаем данные для контекста -------------------
        districts = await sheets_client.list_available_districts() or []
        cities = ["г. Самарканд", "г. Бухара"]  # явные города, которых нет в district
        departments = await sheets_client.get_all_departments()  # список всех клубов, чтобы дать LLM

        # ------------------- Формируем промпт -------------------
        prompt = f"""
Вы — информационный ассистент фитнес-клубов Chekhov Sport Club, женщина по имени Малика.

Контекст пользователя:
- Состояние диалога: {state_data['state']}
- История последних сообщений:
{''.join([f"{m['role'].capitalize()}: {m['content']}\n" for m in state_data['history']])}

Доступные клубы и районы:
- Районы Ташкента: {', '.join(districts)}
- Города: {', '.join(cities)}
- Все клубы: {', '.join([d.get('Name', '') for d in departments])}

Задача:
1. Определить, что хочет пользователь: район, город, клуб или помощь с выбором.
2. Если пользователь просто здоровается или пишет общие фразы, **не повторяй приветствие**, а веди разговор дальше: предложи варианты клубов или помощь с выбором.
3. Если есть совпадение по клубу/району/городу — предложи следующий шаг: выбор времени тренировок, подбор абонемента или запись на презентацию.
4. Ответ дружелюбный, информативный, без выдуманных данных.
5. Если не понятно, предложи пользователю **список доступных вариантов** (районы, города, клубы).
6. Никогда не дублируй, что ты Малика; это уже известно пользователю.
7. Ограничь длину ответа 5-6 предложениями, чтобы диалог оставался живым и удобочитаемым.
"""

        try:
            # ------------------- Вызов LLM -------------------
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Вы информационный ассистент Chekhov Sport Club."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
            )

            answer = response.choices[0].message.content.strip()
            logger.info("Ответ от DeepSeek успешно получен")

            # ------------------- Сохраняем ответ бота в историю -------------------
            self.add_to_history(user_id, "assistant", answer)

            return answer

        except Exception as e:
            logger.exception("Ошибка при обращении к DeepSeek API: %s", e)
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."