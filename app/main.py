import asyncio
import logging

from app.bot import bot, dp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


async def main() -> None:
    """Точка входа приложения.
    Запускает long polling Telegram-бота и начинает
    обработку входящих обновлений."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
