from dataclasses import dataclass
from enum import Enum

class TrainingIntent(Enum):
    CLUBS_BY_CLASS = "CLUBS_BY_CLASS"
    CLASSES_BY_CLUB = "CLASSES_BY_CLUB"
    LIST_ALL_CLASSES = "LIST_ALL_CLASSES"
    UNKNOWN = "UNKNOWN"

@dataclass
class TrainingIntentResult:
    intent: TrainingIntent
    entity: str | None = None

class TrainingIntentDetector:
    def __init__(self, club_names: list[str], class_names: list[str]):
        self.club_names = club_names
        self.class_names = class_names

    def detect(self, text: str) -> TrainingIntentResult:
        # простая логика, например
        text_lower = text.lower()
        for cls in self.class_names:
            if cls.lower() in text_lower:
                return TrainingIntentResult(intent=TrainingIntent.CLUBS_BY_CLASS, entity=cls)
        for club in self.club_names:
            if club.lower() in text_lower:
                return TrainingIntentResult(intent=TrainingIntent.CLASSES_BY_CLUB, entity=club)
        if "тренировк" in text_lower or "занятия" in text_lower:
            return TrainingIntentResult(intent=TrainingIntent.LIST_ALL_CLASSES)
        return TrainingIntentResult(intent=TrainingIntent.UNKNOWN)