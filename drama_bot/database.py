"""SQLite (aiosqlite) bilan ishlash qatlami."""
import logging
from typing import Optional

import aiosqlite

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    lang TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS channels(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('sub','post')),
    UNIQUE(chat_id, kind)
);
CREATE TABLE IF NOT EXISTS dramas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    title_lower TEXT NOT NULL,
    year INTEGER NOT NULL,
    genre TEXT NOT NULL CHECK(genre IN ('action','romance')),
    description TEXT DEFAULT '',
    poster TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dramas_title ON dramas(title_lower);
CREATE INDEX IF NOT EXISTS idx_dramas_genre ON dramas(genre);
CREATE TABLE IF NOT EXISTS episodes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drama_id INTEGER NOT NULL REFERENCES dramas(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    file_id TEXT NOT NULL,
    UNIQUE(drama_id, number)
);
CREATE TABLE IF NOT EXISTS favorites(
    user_id INTEGER NOT NULL,
    drama_id INTEGER NOT NULL REFERENCES dramas(id) ON DELETE CASCADE,
    PRIMARY KEY(user_id, drama_id)
);
"""

EDITABLE = {"title", "year", "genre", "description", "poster"}


def _like(q: str) -> str:
    """LIKE uchun maxsus belgilarni ekranlash."""
    q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{q.casefold()}%"


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: Optional[aiosqlite.Connection] = None
        self._lang_cache: dict[int, Optional[str]] = {}

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA synchronous=NORMAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()
        logging.info("Baza ulandi: %s", self.path)

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    # ---- past darajadagi yordamchilar ----
    async def _one(self, q: str, args: tuple = ()):
        async with self.conn.execute(q, args) as cur:
            return await cur.fetchone()

    async def _all(self, q: str, args: tuple = ()):
        async with self.conn.execute(q, args) as cur:
            return await cur.fetchall()

    async def _exec(self, q: str, args: tuple = ()) -> int:
        cur = await self.conn.execute(q, args)
        await self.conn.commit()
        return cur.lastrowid

    # ---- foydalanuvchilar ----
    async def ensure_user(self, uid: int) -> None:
        await self._exec("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))

    async def get_lang(self, uid: int) -> Optional[str]:
        if uid in self._lang_cache:
            return self._lang_cache[uid]
        row = await self._one("SELECT lang FROM users WHERE user_id=?", (uid,))
        lang = row["lang"] if row else None
        if lang:
            self._lang_cache[uid] = lang
        return lang

    async def set_lang(self, uid: int, lang: str) -> None:
        await self._exec(
            "INSERT INTO users(user_id, lang) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
            (uid, lang),
        )
        self._lang_cache[uid] = lang

    # ---- adminlar ----
    async def admin_ids(self) -> list[int]:
        return [r["user_id"] for r in await self._all("SELECT user_id FROM admins")]

    async def add_admin(self, uid: int) -> None:
        await self._exec("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (uid,))

    async def del_admin(self, uid: int) -> None:
        await self._exec("DELETE FROM admins WHERE user_id=?", (uid,))

    # ---- kanallar ----
    async def get_channels(self, kind: str):
        return await self._all("SELECT * FROM channels WHERE kind=? ORDER BY id", (kind,))

    async def get_channel(self, ch_id: int):
        return await self._one("SELECT * FROM channels WHERE id=?", (ch_id,))

    async def add_channel(self, chat_id: int, title: str, url: str, kind: str) -> bool:
        try:
            await self._exec(
                "INSERT INTO channels(chat_id,title,url,kind) VALUES(?,?,?,?)",
                (chat_id, title, url, kind),
            )
            return True
        except aiosqlite.IntegrityError:
            return False

    async def del_channel(self, ch_id: int) -> None:
        await self._exec("DELETE FROM channels WHERE id=?", (ch_id,))

    # ---- dramalar ----
    async def next_code(self) -> str:
        row = await self._one("SELECT MAX(CAST(code AS INTEGER)) AS m FROM dramas")
        return str((row["m"] or 1000) + 1)

    async def add_drama(self, title, year, genre, description, poster) -> str:
        code = await self.next_code()
        await self._exec(
            "INSERT INTO dramas(code,title,title_lower,year,genre,description,poster) "
            "VALUES(?,?,?,?,?,?,?)",
            (code, title, title.casefold(), year, genre, description, poster),
        )
        return code

    async def get_drama(self, drama_id: int):
        return await self._one("SELECT * FROM dramas WHERE id=?", (drama_id,))

    async def get_drama_by_code(self, code: str):
        return await self._one("SELECT * FROM dramas WHERE code=?", (code,))

    async def search_title(self, q: str, limit: int = 20, offset: int = 0):
        return await self._all(
            "SELECT * FROM dramas WHERE title_lower LIKE ? ESCAPE '\\' "
            "ORDER BY title_lower LIMIT ? OFFSET ?",
            (_like(q), limit, offset),
        )

    async def list_by_genre(self, genre: str, limit: int, offset: int):
        return await self._all(
            "SELECT * FROM dramas WHERE genre=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (genre, limit, offset),
        )

    async def count_by_genre(self, genre: str) -> int:
        row = await self._one("SELECT COUNT(*) c FROM dramas WHERE genre=?", (genre,))
        return row["c"]

    async def update_drama(self, drama_id: int, field: str, value) -> None:
        if field not in EDITABLE:
            raise ValueError("Noto'g'ri maydon")
        await self._exec(f"UPDATE dramas SET {field}=? WHERE id=?", (value, drama_id))
        if field == "title":
            await self._exec(
                "UPDATE dramas SET title_lower=? WHERE id=?", (value.casefold(), drama_id)
            )

    async def delete_drama(self, drama_id: int) -> None:
        await self._exec("DELETE FROM dramas WHERE id=?", (drama_id,))

    # ---- qismlar ----
    async def episode_numbers(self, drama_id: int) -> list[int]:
        rows = await self._all(
            "SELECT number FROM episodes WHERE drama_id=? ORDER BY number", (drama_id,)
        )
        return [r["number"] for r in rows]

    async def get_episode(self, drama_id: int, number: int):
        return await self._one(
            "SELECT * FROM episodes WHERE drama_id=? AND number=?", (drama_id, number)
        )

    async def add_episode(self, drama_id: int, file_id: str) -> int:
        row = await self._one(
            "SELECT COALESCE(MAX(number),0)+1 AS n FROM episodes WHERE drama_id=?",
            (drama_id,),
        )
        number = row["n"]
        await self._exec(
            "INSERT INTO episodes(drama_id,number,file_id) VALUES(?,?,?)",
            (drama_id, number, file_id),
        )
        return number

    async def delete_episode(self, drama_id: int, number: int) -> bool:
        cur = await self.conn.execute(
            "DELETE FROM episodes WHERE drama_id=? AND number=?", (drama_id, number)
        )
        await self.conn.commit()
        return cur.rowcount > 0

    # ---- sevimlilar ----
    async def is_fav(self, uid: int, drama_id: int) -> bool:
        row = await self._one(
            "SELECT 1 FROM favorites WHERE user_id=? AND drama_id=?", (uid, drama_id)
        )
        return row is not None

    async def toggle_fav(self, uid: int, drama_id: int) -> bool:
        """True qaytarsa — qo'shildi, False — olib tashlandi."""
        if await self.is_fav(uid, drama_id):
            await self._exec(
                "DELETE FROM favorites WHERE user_id=? AND drama_id=?", (uid, drama_id)
            )
            return False
        await self._exec(
            "INSERT OR IGNORE INTO favorites(user_id,drama_id) VALUES(?,?)", (uid, drama_id)
        )
        return True

    async def list_favs(self, uid: int, limit: int, offset: int):
        return await self._all(
            "SELECT d.* FROM dramas d JOIN favorites f ON f.drama_id=d.id "
            "WHERE f.user_id=? ORDER BY d.title_lower LIMIT ? OFFSET ?",
            (uid, limit, offset),
        )

    async def count_favs(self, uid: int) -> int:
        row = await self._one("SELECT COUNT(*) c FROM favorites WHERE user_id=?", (uid,))
        return row["c"]


db = Database(DB_PATH)
