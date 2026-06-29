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


USERS_PER_PAGE = 25


def format_user_line(user) -> str:
    username = f"@{user.username}" if user.username else "без username"
    return f"• {user.full_name} ({username}) — <code>{user.telegram_id}</code>"


def build_users_list_text(users: list, page: int = 0, per_page: int = USERS_PER_PAGE) -> tuple[str, int, int]:
    total = len(users)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    chunk = users[page * per_page : (page + 1) * per_page]

    header = LEXICON_RU["admin_users_list"].format(count=total)
    if total_pages > 1:
        header += LEXICON_RU["admin_users_page"].format(page=page + 1, total_pages=total_pages)

    lines = [header, ""]
    lines.extend(format_user_line(user) for user in chunk)
    return "\n".join(lines), page, total_pages


def users_pagination_kb(page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    if total_pages <= 1:
        return None

    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text=LEXICON_RU["btn_users_prev"], callback_data=f"users_page:{page - 1}")
    if page < total_pages - 1:
        builder.button(text=LEXICON_RU["btn_users_next"], callback_data=f"users_page:{page + 1}")
    builder.adjust(2)
    return builder.as_markup()
