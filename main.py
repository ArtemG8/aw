import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import conf
from database import create_db_and_tables, dispose_engine, seed_default_materials
from database.database import async_session_maker
from handlers import setup_routers, set_admin_menu
from keyboards import set_main_menu
from middlewares import DbSessionMiddleware

logger = logging.getLogger(__name__)


def validate_config() -> None:
    if not conf.BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Создайте файл .env по образцу .env.example")
        sys.exit(1)
    if not conf.ADMIN_IDS:
        logger.warning("ADMIN_IDS пуст — ответы пользователям некому будет отправлять")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
        "[%(asctime)s] - %(name)s - %(message)s",
    )

    validate_config()
    logger.info("Starting bot...")

    bot = Bot(token=conf.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(setup_routers())

    try:
        await set_main_menu(bot)
        await set_admin_menu(bot)

        logger.info("Creating database tables if not exist...")
        await create_db_and_tables()
        async with async_session_maker() as session:
            await seed_default_materials(session)
        logger.info("Database tables checked/created.")

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except ConnectionError as exc:
        logger.error("%s", exc)
        sys.exit(1)
