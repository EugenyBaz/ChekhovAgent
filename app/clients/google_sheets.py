import logging
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str):
        """ Конфигурация и инициализация клиента Google Sheets API """
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
        """
        Ищем строку, где Name содержит query (case-insensitive)
        """
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

                if query_lower in name:
                    logger.info("Найден соответствующий департамент: %s", row_dict.get("Name"))
                    return row_dict

            logger.info("Не найден соответсвующий департамент по запросу: %s", query)
            return None

        except Exception as e:
            logger.exception("Ошибка чтения таблицы Google Sheets")
            return None

sheets_client = GoogleSheetsClient(spreadsheet_id=settings.GOOGLE_SHEETS_SPREADSHEET_ID)