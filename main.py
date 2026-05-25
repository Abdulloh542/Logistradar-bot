import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from handlers import user
from utils.db import init_db
from utils.seed import seed_if_empty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    if not Config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN .env faylda ko'rsatilmagan!")

    # DB init
    await init_db()
    await seed_if_empty()

    # Bot
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user.router)

    # Userbot (agar API sozlangan bo'lsa)
    if Config.API_ID and Config.API_HASH and Config.PHONE:
        try:
            from handlers.group import start_userbot
            asyncio.create_task(start_userbot())
            logger.info("Userbot ishga tushdi")
        except ImportError:
            logger.warning("Telethon o'rnatilmagan, userbot ishlamaydi")
    else:
        logger.info("Userbot o'chirilgan — API_ID/API_HASH/PHONE .env da yo'q")

    logger.info("Bot ishga tushdi ✅")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
