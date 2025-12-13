from app.config import settings

if settings.USE_MOCK_LLM:
    from app.services.answer_service_mock import LLMServiceMock as LLMService
else:
    from app.services.answer_service import LLMService