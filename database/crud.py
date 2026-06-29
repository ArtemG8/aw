from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AdminMessageLink, ChatMessage, Material, User




async def seed_default_materials(session: AsyncSession) -> None:
    result = await session.execute(select(Material.id).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    for item in DEFAULT_MATERIALS:
        session.add(Material(**item))
    await session.commit()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
        )
        session.add(user)
    else:
        user.username = username
        user.full_name = full_name

    await session.commit()
    await session.refresh(user)
    return user


async def get_active_materials(session: AsyncSession) -> list[Material]:
    result = await session.execute(
        select(Material)
        .where(Material.is_active.is_(True))
        .order_by(Material.sort_order, Material.id)
    )
    return list(result.scalars().all())


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).where(User.is_blocked.is_(False)).order_by(User.id))
    return list(result.scalars().all())


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def save_chat_message(
    session: AsyncSession,
    user_id: int,
    sender: str,
    text: str | None,
    content_type: str = "text",
    username: str | None = None,
) -> None:
    session.add(
        ChatMessage(
            user_id=user_id,
            username=username,
            sender=sender,
            text=text,
            content_type=content_type,
        )
    )
    await session.commit()


async def save_admin_message_link(
    session: AsyncSession,
    admin_telegram_id: int,
    admin_message_id: int,
    user_telegram_id: int,
) -> None:
    session.add(
        AdminMessageLink(
            admin_telegram_id=admin_telegram_id,
            admin_message_id=admin_message_id,
            user_telegram_id=user_telegram_id,
        )
    )
    await session.commit()


async def get_user_by_admin_reply(
    session: AsyncSession,
    admin_telegram_id: int,
    admin_message_id: int,
) -> int | None:
    result = await session.execute(
        select(AdminMessageLink.user_telegram_id).where(
            AdminMessageLink.admin_telegram_id == admin_telegram_id,
            AdminMessageLink.admin_message_id == admin_message_id,
        )
    )
    return result.scalar_one_or_none()
