import logging
from typing import Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str) -> None:
        self.spreadsheet_id = spreadsheet_id

        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        service = build("sheets", "v4", credentials=credentials)
        self.sheet = service.spreadsheets()

    async def _load_departments(self, sheet_name: str = "all_departments") -> list[dict]:
        """Загружает все отделения из Google Sheets"""
        try:
            result = (
                self.sheet.values()
                .get(spreadsheetId=self.spreadsheet_id, range=sheet_name)
                .execute()
            )

            values = result.get("values", [])
            if not values:
                logger.warning("Google Sheets вернул пустые данные")
                return []

            headers = values[0]
            rows = values[1:]

            return [dict(zip(headers, row)) for row in rows]

        except Exception:
            logger.exception("Ошибка чтения Google Sheets")
            return []

    async def get_all_departments(self, sheet_name: str = "all_departments") -> list[dict]:
        """Возвращает все клубы"""
        return await self._load_departments(sheet_name)

    async def find_department(
        self,
        query: str,
        sheet_name: str = "all_departments",
    ) -> Optional[dict]:
        """Ищет клуб по вхождению Name в query"""
        departments = await self._load_departments(sheet_name)

        query_lower = query.lower()

        for department in departments:
            name = department.get("Name", "").lower()
            if name and name in query_lower:
                logger.info("Найден соответствующий клуб: %s", department.get("Name"))
                return department

        logger.info("Клуб не найден по запросу: %s", query)
        return None

    async def list_available_districts(self, sheet_name: str = "all_departments") -> list[str]:
        """Возвращает уникальные районы Ташкента"""
        departments = await self._load_departments(sheet_name)

        districts = set()

        for dep in departments:
            cell = dep.get("district")
            if not cell:
                continue

            parts = [p.strip().split("(")[0].strip() for p in cell.split("+")]
            districts.update(parts)

        return sorted(districts)

    async def list_available_cities(self, sheet_name: str = "all_departments") -> list[str]:
        """Возвращает уникальные города (кроме Ташкента)"""
        departments = await self._load_departments(sheet_name)

        cities = set()

        for dep in departments:
            address = dep.get("address")
            if not address:
                continue

            city = address.split(",")[-1].strip()
            if city.lower() != "ташкент":
                cities.add(city)

        return sorted(cities)


# Инициализация клиента
sheets_client = GoogleSheetsClient(
    spreadsheet_id=settings.GOOGLE_SHEETS_SPREADSHEET_ID
)

