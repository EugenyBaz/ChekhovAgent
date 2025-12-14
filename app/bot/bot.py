from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.config import settings

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)
