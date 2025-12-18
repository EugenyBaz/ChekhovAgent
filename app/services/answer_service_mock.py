import logging
from typing import List

from app.clients.google_sheets import sheets_client
from app.clients.group_classes import group_classes_client
from app.services.intent_detector import TrainingIntentDetector, TrainingIntent

logger = logging.getLogger(__name__)

class LLMServiceMock:
    """Мок LLM-сервиса для тестирования без реального API, совместим с новой логикой интентов"""

    def __init__(self):
        self.user_states = {}

    def add_to_history(self, user_id: int, role: str, content: str):
        history: List[dict] = self.user_states.setdefault(user_id, {}).setdefault("history", [])
        history.append({"role": role, "content": content})
        if len(history) > 6:
            history.pop(0)

    async def generate_response(self, user_id: int, user_text: str) -> str:
        # инициализация состояния пользователя
        state_data = self.user_states.setdefault(
            user_id,
            {"state": "NEED_CLUB", "club": None, "time_preference": None, "greeted": False, "history": []},
        )

        self.add_to_history(user_id, "user", user_text)

        # Получаем справочники
        departments = await sheets_client.get_all_departments()
        club_names = [d.get("Name", "") for d in departments if d.get("Name")]

        all_classes_data = await group_classes_client.get_all()
        class_names = [row["Name"] for row in all_classes_data]

        # Детектим интент
        detector = TrainingIntentDetector(club_names, class_names)
        intent = detector.detect(user_text)
        entity = getattr(detector, "last_entity", None)

        logger.info(f"[MOCK] Detected intent: {intent}, entity: {entity}")

        # Формируем мок-ответ
        if intent == TrainingIntent.CLUBS_BY_CLASS and entity:
            clubs = await group_classes_client.get_clubs_by_class(entity)
            if clubs:
                info = []
                for c in clubs:
                    club_info = next((d for d in departments if d.get("Name") == c), {})
                    address = club_info.get("address", "Нет данных")
                    phone = club_info.get("phone", "Нет данных")
                    info.append(f"{c} (Адрес: {address}, Телефон: {phone})")
                response = f"[MOCK] Тренировка '{entity}' доступна в клубах: {', '.join(info)}"
            else:
                response = f"[MOCK] Нет клубов с тренировкой '{entity}'"

        elif intent == TrainingIntent.CLASSES_BY_CLUB and entity:
            classes = await group_classes_client.get_classes_by_club(entity)
            club_info = next((d for d in departments if d.get("Name") == entity), {})
            address = club_info.get("address", "Нет данных")
            phone = club_info.get("phone", "Нет данных")
            response = (
                f"[MOCK] Клуб '{entity}'\nАдрес: {address}\nТелефон: {phone}\n"
                f"Доступные тренировки: {', '.join(classes) if classes else 'Нет данных'}"
            )

        elif intent == TrainingIntent.LIST_ALL_CLASSES:
            response = f"[MOCK] Все доступные тренировки: {', '.join(class_names)}"

        else:
            # общий блок фактов
            districts = await sheets_client.list_available_districts() or []
            cities = ["г. Самарканд", "г. Бухара"]
            response = (
                f"[MOCK] Районы Ташкента: {', '.join(districts)}\n"
                f"Города: {', '.join(cities)}\n"
                f"Все клубы: {', '.join(club_names)}\n"
                f"Все тренировки: {', '.join(class_names)}"
            )

        self.add_to_history(user_id, "assistant", response)
        return response