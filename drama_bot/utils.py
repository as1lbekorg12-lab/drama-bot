"""Umumiy yordamchi funksiyalar: rollar, obuna tekshiruvi, xavfsiz tahrirlash."""
import asyncio
import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from database import db

# ---------------- Rollar ----------------
ADMIN_IDS: set[int] = set()


async def load_admins() -> None:
    ADMIN_IDS.clear()
    ADMIN_IDS.update(await db.admin_ids())


def is_owner(uid: int) -> bool:
    return uid == OWNER_ID


def is_admin(uid: int) -> bool:
    """Owner ham admin huquqlariga ega."""
    return uid == OWNER_ID or uid in ADMIN_IDS


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_admin(event.from_user.id)


class IsOwner(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return bool(event.from_user) and is_owner(event.from_user.id)


# ---------------- Majburiy obuna ----------------
_sub_cache: dict[int, float] = {}
SUB_TTL = 60  # soniya: obuna bo'lgan foydalanuvchi qayta tekshirilmaydi


async def _is_member(bot: Bot, chat_id: int, uid: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, uid)
        return member.status not in ("left", "kicked")
    except Exception as e:  # bot kanalda admin emas va hokazo
        logging.warning("Obuna tekshiruvida xato (chat %s): %s", chat_id, e)
        return True  # kanal xatosi foydalanuvchini bloklamasin


async def missing_channels(bot: Bot, uid: int, use_cache: bool = True):
    """Foydalanuvchi obuna bo'lmagan majburiy kanallar ro'yxati."""
    if is_admin(uid):
        return []
    if use_cache and time.monotonic() - _sub_cache.get(uid, 0) < SUB_TTL:
        return []
    channels = await db.get_channels("sub")
    if not channels:
        return []
    results = await asyncio.gather(*(_is_member(bot, c["chat_id"], uid) for c in channels))
    missing = [c for c, ok in zip(channels, results) if not ok]
    if missing:
        _sub_cache.pop(uid, None)
    else:
        _sub_cache[uid] = time.monotonic()
    return missing


# ---------------- Xabarni xavfsiz almashtirish ----------------
async def safe_edit(call: CallbackQuery, text: str, markup=None) -> None:
    """Matnli xabarni tahrirlaydi; rasm/video bo'lsa — o'chirib, yangisini yuboradi."""
    msg = call.message
    if msg.text is not None:
        try:
            await msg.edit_text(text, reply_markup=markup)
            return
        except TelegramBadRequest as e:
            if "not modified" in str(e):
                return
    try:
        await msg.delete()
    except Exception:
        pass
    await msg.answer(text, reply_markup=markup)
