import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeChat, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import conf
from database.crud import get_all_users, get_user_by_admin_reply, get_user_by_telegram_id, save_admin_message_link
from filters import IsAdmin
from keyboards import build_users_list_text, users_pagination_kb
from lexicon import LEXICON_RU
from services.message_relay import send_admin_reply_to_user

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def set_admin_menu(bot, admin_id: int | None = None) -> None:
    commands = [
        BotCommand(command="users", description="Список пользователей"),
        BotCommand(command="broadcast", description="Рассылка всем"),
        BotCommand(command="admin", description="Справка администратора"),
    ]
    admin_ids = [admin_id] if admin_id is not None else conf.ADMIN_IDS

    for current_admin_id in admin_ids:
        try:
            await bot.set_my_commands(
                commands,
                scope=BotCommandScopeChat(chat_id=current_admin_id),
            )
        except TelegramBadRequest:
            logger.warning(
                "Не удалось установить команды для админа %s. "
                "Сначала напишите боту /start с этого аккаунта.",
                current_admin_id,
            )


@router.message(Command("users"))
async def cmd_users(message: Message, session: AsyncSession) -> None:
    users = await get_all_users(session)
    if not users:
        await message.answer(LEXICON_RU["admin_no_users"])
        return

    text, page, total_pages = build_users_list_text(users)
    await message.answer(
        text,
        reply_markup=users_pagination_kb(page, total_pages),
    )


@router.callback_query(F.data.startswith("users_page:"))
async def users_page(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None or callback.message is None:
        await callback.answer()
        return

    page = int(callback.data.split(":", 1)[1])
    users = await get_all_users(session)
    if not users:
        await callback.answer(LEXICON_RU["admin_no_users"], show_alert=True)
        return

    text, page, total_pages = build_users_list_text(users, page=page)
    await callback.message.edit_text(
        text,
        reply_markup=users_pagination_kb(page, total_pages),
    )
    await callback.answer()


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, session: AsyncSession) -> None:
    if not message.text:
        await message.answer(LEXICON_RU["admin_broadcast_usage"])
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(LEXICON_RU["admin_broadcast_usage"])
        return

    text = parts[1]
    users = await get_all_users(session)
    sent = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user.telegram_id, text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        LEXICON_RU["admin_broadcast_done"].format(sent=sent, failed=failed)
    )


@router.message(F.reply_to_message)
async def admin_reply(message: Message, session: AsyncSession) -> None:
    if message.from_user is None or message.reply_to_message is None:
        return

    user_telegram_id = await get_user_by_admin_reply(
        session,
        admin_telegram_id=message.from_user.id,
        admin_message_id=message.reply_to_message.message_id,
    )
    if user_telegram_id is None:
        return

    user = await get_user_by_telegram_id(session, user_telegram_id)
    if user is None:
        await message.answer(LEXICON_RU["admin_user_not_found"])
        return

    success = await send_admin_reply_to_user(
        message.bot,
        session,
        user_telegram_id,
        message,
        user_db_id=user.id,
        username=user.username,
    )
    if success:
        await message.answer(
            LEXICON_RU["admin_reply_sent"].format(name=user.full_name)
        )
        sent = await message.answer(
            f"↩️ Ответ пользователю <b>{user.full_name}</b> (<code>{user.telegram_id}</code>)\n\n"
            f"{LEXICON_RU['admin_reply_hint']}"
        )
        await save_admin_message_link(
            session,
            admin_telegram_id=message.from_user.id,
            admin_message_id=sent.message_id,
            user_telegram_id=user.telegram_id,
        )
    else:
        await message.answer(LEXICON_RU["admin_reply_failed"])


@router.message(Command("admin"))
async def cmd_admin_help(message: Message) -> None:
    await message.answer(
        "<b>Команды администратора:</b>\n"
        "/users — список пользователей\n"
        "/broadcast Текст — рассылка всем\n"
        "/admin — эта справка\n\n"
        "Отвечайте <b>reply</b> на сообщения пользователей, чтобы вести несколько чатов одновременно."
    )
