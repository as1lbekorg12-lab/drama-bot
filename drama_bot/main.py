"""Drama Bot — kirish nuqtasi."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import BOT_TOKEN
from database import db
from handlers import admin, owner, user
from middlewares import SubscriptionMiddleware
from utils import load_admins


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    await db.connect()
    await load_admins()

    # protect_content=True: barcha xabarlar (video, poster) forward/saqlashdan himoyalangan
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML, protect_content=True, link_preview_is_disabled=True
        ),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())

    # Tartib muhim: owner -> admin -> user
    dp.include_routers(owner.router, admin.router, user.router)

    @dp.error()
    async def on_error(event: ErrorEvent) -> bool:
        logging.exception("Kutilmagan xato: %s", event.exception)
        return True

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
