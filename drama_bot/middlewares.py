"""Majburiy obuna middleware: obuna bo'lmagan foydalanuvchini to'xtatadi."""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from database import db
from keyboards import sub_kb
from locales import tr_or_all
from utils import is_admin, missing_channels


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict,
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or is_admin(user.id):
            return await handler(event, data)

        if isinstance(event, Message):
            if event.chat.type != "private":
                return await handler(event, data)
            # /start o'zi obunani tekshiradi
            if event.text and event.text.startswith("/start"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            if event.data == "check_sub":
                return await handler(event, data)

        missing = await missing_channels(data["bot"], user.id)
        if not missing:
            return await handler(event, data)

        lang = await db.get_lang(user.id)
        text = tr_or_all(lang, "sub_required")
        markup = sub_kb(missing, lang)
        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.message.answer(text, reply_markup=markup)
        else:
            await event.answer(text, reply_markup=markup)
        return None
