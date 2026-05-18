import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from shared.config import BOT_TOKEN
from bot_db.database import init_db
from bot_db.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("⚙️ Инициализация базы данных...")
    await init_db()

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("🚀 Бот с БД запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
