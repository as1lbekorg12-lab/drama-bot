"""Inline klaviaturalar (Bot API 9.4 rangli tugmalar: primary / success / danger)."""
from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales import LANGS, tr, tr_or_all

PER_PAGE = 10      # ro'yxatdagi dramalar soni
EP_PER_PAGE = 30   # bir sahifadagi qismlar soni
EP_PER_ROW = 5


def btn(text: str, cb: Optional[str] = None, url: Optional[str] = None,
        style: Optional[str] = None) -> InlineKeyboardButton:
    """style: 'primary' (ko'k), 'success' (yashil), 'danger' (qizil)."""
    data = {"text": text}
    if cb:
        data["callback_data"] = cb
    if url:
        data["url"] = url
    if style:
        data["style"] = style
    return InlineKeyboardButton(**data)


def kb(rows: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------- Foydalanuvchi klaviaturalari ----------------
def lang_kb() -> InlineKeyboardMarkup:
    return kb([
        [btn("🇺🇿 O'zbekcha", "lang:uz", style="primary")],
        [btn("🇷🇺 Русский", "lang:ru", style="primary")],
        [btn("🇬🇧 English", "lang:en", style="primary")],
    ])


def sub_kb(channels, lang) -> InlineKeyboardMarkup:
    rows = [[btn(f"📢 {c['title']}", url=c["url"])] for c in channels]
    rows.append([btn(tr_or_all(lang, "btn_check", " / "), "check_sub", style="success")])
    return kb(rows)


def home_kb(lang) -> InlineKeyboardMarkup:
    return kb([[btn(tr(lang, "btn_home"), "u:home")]])


def main_menu_kb(lang) -> InlineKeyboardMarkup:
    return kb([
        [btn(tr(lang, "btn_code"), "u:code", style="primary")],
        [btn(tr(lang, "btn_name"), "u:name", style="primary")],
        [btn(tr(lang, "btn_genre"), "u:genre", style="success")],
        [btn(tr(lang, "btn_fav"), "fav:0", style="danger")],
    ])


def genre_menu_kb(lang) -> InlineKeyboardMarkup:
    return kb([
        [btn(tr(lang, "genre_action"), "g:action:0", style="danger")],
        [btn(tr(lang, "genre_romance"), "g:romance:0", style="primary")],
        [btn(tr(lang, "btn_home"), "u:home")],
    ])


def list_kb(items, page: int, total: int, nav_prefix: str, lang) -> InlineKeyboardMarkup:
    """Dramalar ro'yxati + sahifalash. nav_prefix: 'g:action' yoki 'fav'."""
    rows = [[btn(f"🎬 {d['title']} ({d['year']})", f"d:{d['id']}")] for d in items]
    nav = []
    if page > 0:
        nav.append(btn("⬅️", f"{nav_prefix}:{page - 1}"))
    if (page + 1) * PER_PAGE < total:
        nav.append(btn("➡️", f"{nav_prefix}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([btn(tr(lang, "btn_home"), "u:home")])
    return kb(rows)


def card_kb(lang, drama_id: int, numbers: list[int], page: int, is_fav: bool) -> InlineKeyboardMarkup:
    rows, row = [], []
    chunk = numbers[page * EP_PER_PAGE:(page + 1) * EP_PER_PAGE]
    for n in chunk:
        row.append(btn(str(n), f"e:{drama_id}:{n}", style="primary"))
        if len(row) == EP_PER_ROW:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(btn("⬅️", f"dp:{drama_id}:{page - 1}"))
    if (page + 1) * EP_PER_PAGE < len(numbers):
        nav.append(btn("➡️", f"dp:{drama_id}:{page + 1}"))
    if nav:
        rows.append(nav)
    if is_fav:
        rows.append([btn(tr(lang, "fav_remove"), f"f:{drama_id}:{page}", style="danger")])
    else:
        rows.append([btn(tr(lang, "fav_add"), f"f:{drama_id}:{page}", style="success")])
    rows.append([btn(tr(lang, "btn_home"), "u:home")])
    return kb(rows)
