import logging
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str) -> None:
        """Конфигурация и инициализация клиента Google Sheets API"""
        self.spreadsheet_id = spreadsheet_id

        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        self.service = build("sheets", "v4", credentials=credentials)
        self.sheet = self.service.spreadsheets()

    async def find_department(
        self,
        query: str,
        sheet_name: str = "all_departments",
    ) -> Optional[dict]:
        """Ищем строку, где Name содержит query"""
        try:
            logger.info("Получение данных из Google Sheets")

            result = (
                self.sheet.values()
                .get(
                    spreadsheetId=self.spreadsheet_id,
                    range=sheet_name,
                )
                .execute()
            )

            values = result.get("values", [])
            if not values:
                logger.warning("Google Sheets вернул пустые данные")
                return None

            headers = values[0]
            rows = values[1:]

            query_lower = query.lower()

            for row in rows:
                row_dict = dict(zip(headers, row))
                name = row_dict.get("Name", "").lower()

                if name in query_lower:
                    logger.info("Найден соответствующий клуб: %s", row_dict.get("Name"))
                    return row_dict

            logger.info("Не найден соответствующий клуб по запросу: %s", query)
            return None

        except Exception:
            logger.exception("Ошибка чтения таблицы Google Sheets")
            return None

    async def list_available_districts(self, sheet_name: str = "all_departments") -> list[str]:
        """Возвращает уникальные районы Ташкента из столбца district"""
        try:
            result = (
                self.sheet.values()
                .get(spreadsheetId=self.spreadsheet_id, range=sheet_name)
                .execute()
            )
            values = result.get("values", [])
            if not values:
                return []

            headers = values[0]
            rows = values[1:]

            district_idx = headers.index("district")
            districts_set = set()

            for row in rows:
                if len(row) <= district_idx:
                    continue
                cell = row[district_idx]
                if not cell:
                    continue
                parts = [p.strip().split("(")[0].strip() for p in cell.split("+")]
                districts_set.update(parts)

            return sorted(districts_set)

        except Exception:
            logger.exception("Ошибка получения списка районов из Google Sheets")
            return []

    async def list_available_cities(self, sheet_name: str = "all_departments") -> list[str]:
        """Возвращает уникальные города из столбца address, кроме Ташкента"""
        try:
            result = (
                self.sheet.values()
                .get(spreadsheetId=self.spreadsheet_id, range=sheet_name)
                .execute()
            )
            values = result.get("values", [])
            if not values:
                return []

            headers = values[0]
            rows = values[1:]

            address_idx = headers.index("address")
            cities_set = set()

            for row in rows:
                if len(row) <= address_idx:
                    continue
                cell = row[address_idx]
                if not cell:
                    continue
                city = cell.split(",")[-1].strip()
                if city.lower() != "ташкент":
                    cities_set.add(city)

            return sorted(cities_set)

        except Exception:
            logger.exception("Ошибка получения списка городов из Google Sheets")
            return []

    async def get_all_departments(self, sheet_name: str = "all_departments") -> list[dict]:
        """Возвращает список всех клубов как словари {Name, address, phone, Notes, district}"""
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
            departments = [dict(zip(headers, row)) for row in rows]
            return departments

        except Exception:
            logger.exception("Ошибка при чтении таблицы Google Sheets")
            return []


# Инициализация клиента
sheets_client = GoogleSheetsClient(spreadsheet_id=settings.GOOGLE_SHEETS_SPREADSHEET_ID)


