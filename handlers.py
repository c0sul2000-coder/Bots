from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from . import database as db
from .keyboards import profile_keyboard, confirm_delete_keyboard, back_keyboard

router = Router()


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    is_new = await db.register_user(user.id, user.username, user.full_name)

    if is_new:
        text = (
            f"🎉 Добро пожаловать, <b>{user.full_name}</b>!\n\n"
            "Ты успешно зарегистрирован(а). Я запоминаю твои сообщения и веду статистику.\n\n"
            "Напиши мне что-нибудь, и я сохраню это в историю!"
        )
    else:
        text = (
            f"👋 С возвращением, <b>{user.full_name}</b>!\n\n"
            "Используй /profile для просмотра профиля."
        )
    await message.answer(text, parse_mode="HTML")


# ── /profile ─────────────────────────────────────────────────────────────────

@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await show_profile(message.from_user.id, message)


async def show_profile(user_id: int, target: Message | CallbackQuery) -> None:
    user = await db.get_user(user_id)
    if not user:
        text = "❌ Ты не зарегистрирован. Напиши /start"
        if isinstance(target, Message):
            await target.answer(text)
        else:
            await target.message.edit_text(text)
        return

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"📛 Имя: {user['full_name']}\n"
        f"🔖 Username: @{user['username'] or '—'}\n"
        f"📅 Дата регистрации: {user['registered_at']}\n"
        f"✉️ Сообщений записано: <b>{user['message_count']}</b>"
    )
    if isinstance(target, Message):
        await target.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")
    else:
        await target.message.edit_text(text, reply_markup=profile_keyboard(), parse_mode="HTML")


# ── /stats ────────────────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    stats = await db.get_stats()
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats['total_users']}</b>\n"
        f"✉️ Сохранено сообщений: <b>{stats['total_messages']}</b>",
        parse_mode="HTML",
    )


# ── Callbacks ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery) -> None:
    await show_profile(callback.from_user.id, callback)
    await callback.answer()


@router.callback_query(F.data == "history")
async def cb_history(callback: CallbackQuery) -> None:
    messages = await db.get_history(callback.from_user.id, limit=5)
    if not messages:
        text = "📜 История пуста. Напиши мне что-нибудь!"
    else:
        lines = [f"<b>Последние {len(messages)} сообщений:</b>\n"]
        for i, m in enumerate(messages, 1):
            lines.append(f"{i}. [{m['created_at']}]\n   {m['message']}")
        text = "\n".join(lines)

    await callback.message.edit_text(
        text, reply_markup=back_keyboard(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery) -> None:
    stats = await db.get_stats()
    await callback.message.edit_text(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats['total_users']}</b>\n"
        f"✉️ Сохранено сообщений: <b>{stats['total_messages']}</b>",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "delete_confirm")
async def cb_delete_confirm(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "⚠️ <b>Удалить все твои данные?</b>\n\nЭто действие необратимо.",
        reply_markup=confirm_delete_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "delete_yes")
async def cb_delete_yes(callback: CallbackQuery) -> None:
    deleted = await db.delete_user(callback.from_user.id)
    if deleted:
        await callback.message.edit_text(
            "✅ Все твои данные удалены. Напиши /start чтобы зарегистрироваться снова."
        )
    else:
        await callback.message.edit_text("❌ Данные не найдены.")
    await callback.answer()


@router.callback_query(F.data == "delete_no")
async def cb_delete_no(callback: CallbackQuery) -> None:
    await show_profile(callback.from_user.id, callback)
    await callback.answer("Отменено")


# ── Обычные сообщения — сохраняем в историю ──────────────────────────────────

@router.message()
async def handle_message(message: Message) -> None:
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user:
        await message.answer("Сначала напиши /start для регистрации.")
        return

    await db.save_message(user_id, message.text or "[не текст]")
    await db.increment_message_count(user_id)

    await message.answer(
        f"✅ Сообщение сохранено! (всего: {user['message_count'] + 1})\n\n"
        "📋 /profile — твой профиль\n"
        "📊 /stats — статистика бота",
    )
