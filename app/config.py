import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str

    GOOGLE_SERVICE_ACCOUNT_JSON: str
    GOOGLE_SHEETS_SPREADSHEET_ID: str

    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "True").lower() in (
        "1",
        "true",
        "yes",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
