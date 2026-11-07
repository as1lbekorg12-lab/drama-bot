"""Foydalanuvchi bo'limi: obuna, til, qidiruv, janr, sevimlilar, qismlarni ko'rish."""
import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from keyboards import (PER_PAGE, btn, card_kb, genre_menu_kb, home_kb, kb, lang_kb,
                       list_kb, main_menu_kb, sub_kb)
from locales import CHOOSE_LANG, LANGS, tr, tr_or_all
from states import UserSG
from utils import missing_channels, safe_edit

router = Router(name="user")
GENRES = ("action", "romance")


async def lang_of(uid: int) -> str:
    return await db.get_lang(uid) or "uz"


async def render_card(bot: Bot, chat_id: int, drama, lang: str, uid: int, page: int = 0) -> None:
    """Drama kartochkasini (poster + ma'lumot + qismlar tugmalari) yuboradi."""
    nums = await db.episode_numbers(drama["id"])
    fav = await db.is_fav(uid, drama["id"])
    desc = html.escape((drama["description"] or "")[:600])
    if not nums:
        desc = (desc + "\n\n" if desc else "") + tr(lang, "no_eps")
    caption = tr(
        lang, "card",
        title=html.escape(drama["title"]), year=drama["year"],
        genre=tr(lang, f"genre_{drama['genre']}"), code=drama["code"],
        count=len(nums), desc=desc,
    )
    await bot.send_photo(
        chat_id, drama["poster"], caption=caption[:1024],
        reply_markup=card_kb(lang, drama["id"], nums, page, fav),
    )


# ---------------- /start, obuna, til ----------------
@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext, bot: Bot):
    await state.clear()
    uid = m.from_user.id
    await db.ensure_user(uid)
    missing = await missing_channels(bot, uid)
    if missing:
        lang = await db.get_lang(uid)
        await m.answer(tr_or_all(lang, "sub_required"), reply_markup=sub_kb(missing, lang))
        return
    await m.answer(CHOOSE_LANG, reply_markup=lang_kb())


@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery, bot: Bot):
    uid = call.from_user.id
    missing = await missing_channels(bot, uid, use_cache=False)
    if missing:
        lang = await db.get_lang(uid)
        await call.answer(tr_or_all(lang, "sub_still", " / "), show_alert=True)
        return
    await call.answer()
    await safe_edit(call, CHOOSE_LANG, lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def set_language(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    if lang not in LANGS:
        await call.answer()
        return
    await state.clear()
    await db.set_lang(call.from_user.id, lang)
    await call.answer()
    await safe_edit(call, tr(lang, "menu"), main_menu_kb(lang))


@router.callback_query(F.data == "u:home")
async def go_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await lang_of(call.from_user.id)
    await call.answer()
    await safe_edit(call, tr(lang, "menu"), main_menu_kb(lang))


# ---------------- Qidiruv ----------------
@router.callback_query(F.data == "u:code")
async def ask_code(call: CallbackQuery, state: FSMContext):
    lang = await lang_of(call.from_user.id)
    await state.set_state(UserSG.by_code)
    await call.answer()
    await safe_edit(call, tr(lang, "ask_code"), home_kb(lang))


@router.callback_query(F.data == "u:name")
async def ask_name(call: CallbackQuery, state: FSMContext):
    lang = await lang_of(call.from_user.id)
    await state.set_state(UserSG.by_name)
    await call.answer()
    await safe_edit(call, tr(lang, "ask_name"), home_kb(lang))


@router.message(UserSG.by_code, F.text)
async def search_by_code(m: Message, state: FSMContext, bot: Bot):
    lang = await lang_of(m.from_user.id)
    drama = await db.get_drama_by_code(m.text.strip())
    if not drama:
        await m.answer(tr(lang, "not_found"), reply_markup=home_kb(lang))
        return
    await state.clear()
    try:
        await render_card(bot, m.chat.id, drama, lang, m.from_user.id)
    except TelegramAPIError as e:
        logging.error("Kartochka yuborishda xato: %s", e)
        await m.answer(tr(lang, "error"), reply_markup=home_kb(lang))


@router.message(UserSG.by_name, F.text)
async def search_by_name(m: Message, state: FSMContext):
    lang = await lang_of(m.from_user.id)
    results = await db.search_title(m.text.strip(), limit=20)
    if not results:
        await m.answer(tr(lang, "not_found"), reply_markup=home_kb(lang))
        return
    await state.clear()
    rows = [[btn(f"🎬 {d['title']} ({d['year']})", f"d:{d['id']}")] for d in results]
    rows.append([btn(tr(lang, "btn_home"), "u:home")])
    await m.answer(tr(lang, "results"), reply_markup=kb(rows))


@router.message(UserSG.by_code)
@router.message(UserSG.by_name)
async def text_only(m: Message):
    await m.answer(tr(await lang_of(m.from_user.id), "text_only"))


# ---------------- Janr ----------------
@router.callback_query(F.data == "u:genre")
async def genre_menu(call: CallbackQuery):
    lang = await lang_of(call.from_user.id)
    await call.answer()
    await safe_edit(call, tr(lang, "genre_pick"), genre_menu_kb(lang))


@router.callback_query(F.data.startswith("g:"))
async def genre_list(call: CallbackQuery):
    lang = await lang_of(call.from_user.id)
    try:
        _, genre, page = call.data.split(":")
        page = int(page)
    except ValueError:
        await call.answer()
        return
    if genre not in GENRES:
        await call.answer()
        return
    total = await db.count_by_genre(genre)
    if total == 0:
        await call.answer(tr(lang, "empty_list"), show_alert=True)
        return
    items = await db.list_by_genre(genre, PER_PAGE, page * PER_PAGE)
    await call.answer()
    await safe_edit(
        call, tr(lang, "genre_list", genre=tr(lang, f"genre_{genre}")),
        list_kb(items, page, total, f"g:{genre}", lang),
    )


# ---------------- Sevimlilar ----------------
@router.callback_query(F.data.startswith("fav:"))
async def favorites(call: CallbackQuery):
    uid = call.from_user.id
    lang = await lang_of(uid)
    try:
        page = int(call.data.split(":")[1])
    except ValueError:
        await call.answer()
        return
    total = await db.count_favs(uid)
    if total == 0:
        await call.answer(tr(lang, "fav_empty"), show_alert=True)
        return
    items = await db.list_favs(uid, PER_PAGE, page * PER_PAGE)
    await call.answer()
    await safe_edit(call, tr(lang, "fav_title"), list_kb(items, page, total, "fav", lang))


@router.callback_query(F.data.startswith("f:"))
async def toggle_favorite(call: CallbackQuery):
    uid = call.from_user.id
    lang = await lang_of(uid)
    try:
        _, did, page = call.data.split(":")
        did, page = int(did), int(page)
    except ValueError:
        await call.answer()
        return
    if not await db.get_drama(did):
        await call.answer(tr(lang, "not_found"), show_alert=True)
        return
    added = await db.toggle_fav(uid, did)
    await call.answer(tr(lang, "fav_added" if added else "fav_removed"))
    nums = await db.episode_numbers(did)
    try:
        await call.message.edit_reply_markup(reply_markup=card_kb(lang, did, nums, page, added))
    except TelegramAPIError as e:
        logging.warning("Klaviaturani yangilab bo'lmadi: %s", e)


# ---------------- Drama kartochkasi va qismlar ----------------
@router.callback_query(F.data.startswith("d:"))
async def open_drama(call: CallbackQuery, bot: Bot):
    uid = call.from_user.id
    lang = await lang_of(uid)
    try:
        did = int(call.data.split(":")[1])
    except ValueError:
        await call.answer()
        return
    drama = await db.get_drama(did)
    if not drama:
        await call.answer(tr(lang, "not_found"), show_alert=True)
        return
    await call.answer()
    try:
        await call.message.delete()
    except TelegramAPIError:
        pass
    try:
        await render_card(bot, call.message.chat.id, drama, lang, uid)
    except TelegramAPIError as e:
        logging.error("Kartochka yuborishda xato: %s", e)
        await bot.send_message(call.message.chat.id, tr(lang, "error"), reply_markup=home_kb(lang))


@router.callback_query(F.data.startswith("dp:"))
async def episodes_page(call: CallbackQuery):
    uid = call.from_user.id
    lang = await lang_of(uid)
    try:
        _, did, page = call.data.split(":")
        did, page = int(did), int(page)
    except ValueError:
        await call.answer()
        return
    nums = await db.episode_numbers(did)
    fav = await db.is_fav(uid, did)
    await call.answer()
    try:
        await call.message.edit_reply_markup(reply_markup=card_kb(lang, did, nums, page, fav))
    except TelegramAPIError as e:
        logging.warning("Sahifani almashtirib bo'lmadi: %s", e)


@router.callback_query(F.data.startswith("e:"))
async def send_episode(call: CallbackQuery, bot: Bot):
    lang = await lang_of(call.from_user.id)
    try:
        _, did, num = call.data.split(":")
        did, num = int(did), int(num)
    except ValueError:
        await call.answer()
        return
    drama = await db.get_drama(did)
    episode = await db.get_episode(did, num)
    if not drama or not episode:
        await call.answer(tr(lang, "ep_missing"), show_alert=True)
        return
    await call.answer()
    try:
        # protect_content=True (DefaultBotProperties orqali) — forward/saqlash cheklangan
        await bot.send_video(
            call.message.chat.id, episode["file_id"],
            caption=tr(lang, "ep_caption", title=html.escape(drama["title"]), n=num),
        )
    except TelegramAPIError as e:
        logging.error("Videoni yuborishda xato: %s", e)
        await bot.send_message(call.message.chat.id, tr(lang, "error"))
