import logging
from enum import Enum
from typing import List

from openai import OpenAI

from app.clients.google_sheets import sheets_client
from app.clients.group_classes import group_classes_client
from app.config import settings
from app.services.intent_detector import TrainingIntentDetector, TrainingIntent, TrainingIntentResult

logger = logging.getLogger(__name__)

# ------------------- Состояния диалога -------------------
class DialogState(str, Enum):
    NEED_CLUB = "NEED_CLUB"
    NEED_TIME = "NEED_TIME"
    PRICING = "PRICING"
    CLOSING = "CLOSING"


# ------------------- Сервис LLM -------------------
class LLMService:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.user_states = {}

    # ------------------- История -------------------
    def add_to_history(self, user_id: int, role: str, content: str):
        history: List[dict] = self.user_states.setdefault(user_id, {}).setdefault("history", [])
        history.append({"role": role, "content": content})
        if len(history) > 6:
            history.pop(0)

    # ------------------- Генерация ответа -------------------
    async def generate_response(self, user_id: int, user_text: str) -> str:
        state_data = self.user_states.setdefault(
            user_id,
            {
                "state": DialogState.NEED_CLUB,
                "club": None,
                "time_preference": None,
                "greeted": False,
                "history": [],
            },
        )

        # сохраняем сообщение пользователя
        self.add_to_history(user_id, "user", user_text)

        # получаем справочники
        departments = await sheets_client.get_all_departments()
        # очищаем данные (убираем кавычки, лишние пробелы и переносы строк)
        for d in departments:
            for key in ["Name", "address", "phone"]:
                if d.get(key):
                    d[key] = d[key].replace('"', '').replace('\n', ' ').strip()

        club_names = [d.get("Name") for d in departments if d.get("Name")]

        # Получаем все тренировки из group_classes
        all_classes_data = await group_classes_client.get_all()
        class_names = [row["Name"].strip() for row in all_classes_data]

        # детектим интент
        detector = TrainingIntentDetector(club_names, class_names)
        result: TrainingIntentResult = detector.detect(user_text)
        intent = result.intent
        entity = result.entity

        logger.info("Detected intent: %s, entity: %s", intent, entity)

        # поиск клуба по неполному совпадению (fallback)
        matched_club_info = None
        if entity and intent in [TrainingIntent.CLASSES_BY_CLUB, TrainingIntent.CLUBS_BY_CLASS]:
            # ищем точное совпадение
            matched_club_info = next((d for d in departments if d.get("Name").lower() == entity.lower()), None)
            # если точного нет, ищем частичное совпадение
            if not matched_club_info:
                matched_club_info = next((d for d in departments if entity.lower() in d.get("Name", "").lower()), None)
            if matched_club_info:
                entity = matched_club_info.get("Name")  # обновляем entity на точное имя

        #  формируем факты для LLM
        facts_block = ""

        if intent == TrainingIntent.CLUBS_BY_CLASS and entity:
            clubs = await group_classes_client.get_clubs_by_class(entity)
            clubs_info = []
            for c in clubs:
                club_info = next((d for d in departments if d.get("Name") == c), None)
                if club_info:
                    address = club_info.get("address", "Нет данных")
                    phone = club_info.get("phone", "Нет данных")
                    clubs_info.append(f"{c} (Адрес: {address}, Телефон: {phone})")
            facts_block = f"Тренировка: {entity}\nПроводится в клубах: {', '.join(clubs_info) if clubs_info else 'Нет данных'}"

        elif intent == TrainingIntent.CLASSES_BY_CLUB and entity:
            classes = await group_classes_client.get_classes_by_club(entity)
            address = matched_club_info.get("address", "Нет данных") if matched_club_info else "Нет данных"
            phone = matched_club_info.get("phone", "Нет данных") if matched_club_info else "Нет данных"
            facts_block = (
                f"Клуб: {entity}\nАдрес: {address}\nТелефон: {phone}\n"
                f"Доступные тренировки: {', '.join(classes) if classes else 'Нет данных'}"
            )

        elif intent == TrainingIntent.LIST_ALL_CLASSES:
            all_classes = [row["Name"] for row in all_classes_data]
            facts_block = f"Все доступные тренировки: {', '.join(all_classes)}"

        else:
            districts = await sheets_client.list_available_districts() or []
            cities = ["г. Самарканд", "г. Бухара"]
            facts_block = (
                f"Районы Ташкента: {', '.join(districts)}\n"
                f"Города: {', '.join(cities)}\n"
                f"Все клубы: {', '.join(club_names)}\n"
                f"Все тренировки: {', '.join(class_names)}"
            )

        #  формируем prompt
        prompt = f"""
    Вы — менеджер по продажам фитнес-клубов Chekhov Sport Club, женщина по имени Малика.

    Контекст пользователя:
    - Состояние диалога: {state_data['state']}
    - Обнаруженный интент: {intent}
    - История последних сообщений:
    {''.join([f"{m['role'].capitalize()}: {m['content']}\n" for m in state_data['history']])}

    Факты:
    {facts_block}

    Правила:
    - Повторно не нужно здороваться
    - Используй только переданные факты
    - Не делай предположений
    - Используй только переданные точные данные о клубах, адресах и телефонах. Не придумывай ничего
    - Если данных не хватает — попроси уточнение

    Задача:
    - Корректно ответь пользователю согласно интенту
    - Предложи следующий логичный шаг
    - Ответ 5–6 предложений
    """

        # вызов LLM
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Вы информационный ассистент Chekhov Sport Club."},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            answer = response.choices[0].message.content.strip()
            self.add_to_history(user_id, "assistant", answer)
            return answer

        except Exception as e:
            logger.exception("Ошибка при обращении к DeepSeek API: %s", e)
            return "Извините, произошла ошибка. Попробуйте позже."