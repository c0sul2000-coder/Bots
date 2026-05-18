"""
Асинхронная работа с SQLite через aiosqlite.
Таблицы:
  users   — профили пользователей
  history — история сообщений

Путь к БД берётся из переменной окружения DB_PATH.
На Railway примонтируй Volume на /app/data — тогда данные
сохранятся между перезапусками.
"""
import os
import aiosqlite
from pathlib import Path

# Локально: файл рядом с модулем. На Railway: /app/data/bot_data.db
_default = Path(__file__).parent / "bot_data.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_default)))


async def init_db() -> None:
    """Создать таблицы при первом запуске."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                registered_at TEXT DEFAULT (datetime('now','localtime')),
                message_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                message     TEXT,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()


async def register_user(user_id: int, username: str | None, full_name: str) -> bool:
    """Зарегистрировать пользователя. Возвращает True, если новый."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return False  # уже есть
        await db.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username or "", full_name),
        )
        await db.commit()
        return True


async def get_user(user_id: int) -> dict | None:
    """Получить профиль пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def increment_message_count(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET message_count = message_count + 1 WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()


async def save_message(user_id: int, text: str) -> None:
    """Сохранить сообщение в историю."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, message) VALUES (?, ?)",
            (user_id, text[:500]),  # обрезаем до 500 символов
        )
        await db.commit()


async def get_history(user_id: int, limit: int = 5) -> list[dict]:
    """Получить последние N сообщений пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT message, created_at FROM history WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_stats() -> dict:
    """Общая статистика бота."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur_users = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cur_users.fetchone())[0]

        cur_msgs = await db.execute("SELECT COUNT(*) FROM history")
        total_msgs = (await cur_msgs.fetchone())[0]

        return {"total_users": total_users, "total_messages": total_msgs}


async def delete_user(user_id: int) -> bool:
    """Удалить пользователя и его историю."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
        return True
