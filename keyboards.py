from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📜 История",     callback_data="history"),
        InlineKeyboardButton(text="📊 Статистика",  callback_data="stats"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить данные", callback_data="delete_confirm"),
    )
    return builder.as_markup()


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить",  callback_data="delete_yes"),
        InlineKeyboardButton(text="❌ Отмена",        callback_data="delete_no"),
    )
    return builder.as_markup()


def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 К профилю", callback_data="profile"))
    return builder.as_markup()
