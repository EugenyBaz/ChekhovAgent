from unittest.mock import AsyncMock, patch

import pytest

from app.services.answer_service_mock import LLMServiceMock


@pytest.mark.asyncio
async def test_generate_response_found():
    mock_department = {
        "Name": "Chekhov Sport",
        "address": "г.Ташкент, Мирабадский район, ул. Фидокор, 40/1",
        "phone": "998 90 929-20-00",
        "Notes": "",
    }

    llm_service = LLMServiceMock()

    # Мокаем Google Sheets метод
    with patch(
        "app.clients.google_sheets.sheets_client.find_department",
        new=AsyncMock(return_value=mock_department),
    ):
        response = await llm_service.generate_response("Chekhov Sport")
        assert "[MOCK]" in response
        assert "Chekhov Sport" in response
        assert "г.Ташкент" in response


@pytest.mark.asyncio
async def test_generate_response_not_found():
    llm_service = LLMServiceMock()

    # Мокаем Google Sheets метод — возвращаем None
    with patch(
        "app.clients.google_sheets.sheets_client.find_department",
        new=AsyncMock(return_value=None),
    ):
        response = await llm_service.generate_response("НеСуществующийКлуб")
        assert response == "Не нашёл такую запись в таблице. Попробуйте уточнить запрос."
