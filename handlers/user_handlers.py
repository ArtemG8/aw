from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import conf
from database.crud import get_active_materials, get_or_create_user
from handlers.admin_handlers import set_admin_menu
from keyboards import chat_menu_kb, main_menu_kb, materials_inline_kb
from lexicon import LEXICON_RU
from services.message_relay import notify_admins_about_user_message
from states import ChatFSM

router = Router()


async def _register_user(message: Message, session: AsyncSession):
    user = message.from_user
    if user is None:
        return None
    return await get_or_create_user(
        session,
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )


async def send_welcome(message: Message, session: AsyncSession) -> None:
    materials = await get_active_materials(session)
    text_lines = [
        f"<b>{LEXICON_RU['welcome_title']}</b>",
        LEXICON_RU["welcome_body"],
    ]

    if materials:
        text_lines.append("")
        text_lines.append(LEXICON_RU["materials_header"])
        for material in materials:
            line = f"• <a href=\"{material.url}\">{material.title}</a>"
            if material.description:
                line += f" — {material.description}"
            text_lines.append(line)
    else:
        text_lines.append("")
        text_lines.append(LEXICON_RU["no_materials"])

    await message.answer(
        "\n".join(text_lines),
        reply_markup=main_menu_kb(),
        disable_web_page_preview=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    db_user = await _register_user(message, session)
    if db_user and db_user.is_blocked:
        await message.answer(LEXICON_RU["blocked_user"])
        return

    await state.clear()
    await send_welcome(message, session)

    if message.from_user and message.from_user.id in conf.ADMIN_IDS:
        await set_admin_menu(message.bot, admin_id=message.from_user.id)


@router.message(Command("materials"))
@router.message(lambda m: m.text == LEXICON_RU["btn_materials"])
async def show_materials(message: Message, session: AsyncSession) -> None:
    materials = await get_active_materials(session)
    if not materials:
        await message.answer(LEXICON_RU["no_materials"], reply_markup=main_menu_kb())
        return

    text_lines = [LEXICON_RU["materials_header"], ""]
    for material in materials:
        line = f"• <a href=\"{material.url}\">{material.title}</a>"
        if material.description:
            line += f" — {material.description}"
        text_lines.append(line)

    await message.answer(
        "\n".join(text_lines),
        reply_markup=materials_inline_kb(materials) or main_menu_kb(),
        disable_web_page_preview=True,
    )


@router.message(Command("contact"))
@router.message(lambda m: m.text == LEXICON_RU["btn_contact"])
async def start_contact(message: Message, state: FSMContext, session: AsyncSession) -> None:
    db_user = await _register_user(message, session)
    if db_user and db_user.is_blocked:
        await message.answer(LEXICON_RU["blocked_user"])
        return

    await state.set_state(ChatFSM.waiting_message)
    await message.answer(LEXICON_RU["contact_started"], reply_markup=chat_menu_kb())


@router.message(lambda m: m.text == LEXICON_RU["btn_menu"])
async def back_to_menu(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await message.answer(LEXICON_RU["contact_closed"], reply_markup=main_menu_kb())
    await send_welcome(message, session)


@router.message(StateFilter(ChatFSM.waiting_message))
async def user_chat_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    db_user = await _register_user(message, session)
    if db_user is None:
        return

    if db_user.is_blocked:
        await state.clear()
        await message.answer(LEXICON_RU["blocked_user"], reply_markup=main_menu_kb())
        return

    supported = bool(
        message.text
        or message.photo
        or message.document
        or message.voice
        or message.video
    )
    if not supported:
        await message.answer(LEXICON_RU["unsupported_content"])
        return

    await notify_admins_about_user_message(message.bot, session, db_user.id, message)
    await message.answer(LEXICON_RU["message_sent"], reply_markup=chat_menu_kb())
