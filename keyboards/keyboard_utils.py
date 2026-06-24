from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from lexicon import LEXICON_RU


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=LEXICON_RU["btn_materials"])
    builder.button(text=LEXICON_RU["btn_contact"])
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def chat_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=LEXICON_RU["btn_menu"])
    return builder.as_markup(resize_keyboard=True)


def materials_inline_kb(materials: list) -> InlineKeyboardMarkup | None:
    if not materials:
        return None

    builder = InlineKeyboardBuilder()
    for material in materials:
        builder.button(text=material.title, url=material.url)
    builder.adjust(1)
    return builder.as_markup()


def users_inline_kb(users: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users[:30]:
        label = user.full_name or str(user.telegram_id)
        if user.username:
            label = f"{label} (@{user.username})"
        builder.button(
            text=label[:60],
            callback_data=f"admin_chat:{user.telegram_id}",
        )
    builder.adjust(1)
    return builder.as_markup()
