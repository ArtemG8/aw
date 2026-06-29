import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import conf
from database.models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(
    conf.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"timeout": 10},
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def wait_for_database(retries: int = 10, delay: float = 2.0) -> None:
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection established.")
            return
        except Exception as exc:
            last_error = exc
            logger.warning(
                "PostgreSQL недоступен (попытка %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                await asyncio.sleep(delay)

    raise ConnectionError(
        "Не удалось подключиться к PostgreSQL.\n"
        f"Хост: {conf.DB_HOST}:{conf.DB_PORT}, БД: {conf.DB_NAME}, пользователь: {conf.DB_USER}\n\n"
        "Проверьте:\n"
        "1. Служба PostgreSQL запущена (services.msc → postgresql)\n"
        "2. В .env верные DB_USER, DB_PASS, DB_NAME\n"
        "3. Пользователь и база созданы — выполните scripts/init_db.sql в pgAdmin или psql\n\n"
        f"Последняя ошибка: {last_error}"
    ) from last_error


async def create_db_and_tables() -> None:
    await wait_for_database()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE chat_messages "
                "ADD COLUMN IF NOT EXISTS username VARCHAR(255)"
            )
        )


async def dispose_engine() -> None:
    await engine.dispose()
