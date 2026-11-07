"""Admin paneli: drama/qism boshqaruvi, tahrirlash va kanalga post qilish.
Admin interfeysi o'zbek tilida."""
import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import MAIN_CHANNEL_URL
from database import db
from keyboards import btn, kb
from locales import TEXTS
from states import AddDrama, AddEp, DelDrama, DelEp, EditDrama, PostSG
from utils import IsAdmin, is_owner, safe_edit

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

GENRE_UZ = {"action": TEXTS["uz"]["genre_action"], "romance": TEXTS["uz"]["genre_romance"]}
EDIT_FIELDS = {
    "title": "📝 Nomi", "year": "📅 Yili", "genre": "🎭 Janri",
    "description": "📄 Tavsifi", "poster": "🖼 Rasmi",
}


# ---------------- Yordamchi klaviaturalar ----------------
def panel_kb(uid: int):
    rows = [
        [btn("➕ Drama qo'shish", "adm:add", style="success"),
         btn("🗑 Drama o'chirish", "adm:deldrama", style="danger")],
        [btn("🎞 Qism qo'shish", "adm:addep", style="success"),
         btn("❌ Qism o'chirish", "adm:delep", style="danger")],
        [btn("✏️ Dramani tahrirlash", "adm:edit", style="primary")],
        [btn("📤 Post qilish", "adm:post", style="primary")],
    ]
    if is_owner(uid):
        rows += [
            [btn("📢 Majburiy obuna kanallari", "own:ch:sub")],
            [btn("📣 Post kanallari", "own:ch:post")],
            [btn("👮 Adminlar", "own:adm")],
        ]
    return kb(rows)


def cancel_kb():
    return kb([[btn("❌ Bekor qilish", "adm:menu", style="danger")]])


def back_kb():
    return kb([[btn("⬅️ Admin panel", "adm:menu")]])


def genre_kb(prefix: str):
    return kb([
        [btn(GENRE_UZ["action"], f"{prefix}:action", style="danger"),
         btn(GENRE_UZ["romance"], f"{prefix}:romance", style="primary")],
        [btn("❌ Bekor qilish", "adm:menu", style="danger")],
    ])


def drama_line(d) -> str:
    return f"<b>{html.escape(d['title'])}</b> ({d['year']}) — kod: <code>{d['code']}</code>"


# ---------------- Panel ----------------
@router.message(CommandStart())
async def cmd_start_admin(m: Message, state: FSMContext, bot: Bot):
    """Admin FSM jarayonida /start bosilsa, matn sifatida qabul qilinib qolmasligi uchun."""
    from handlers.user import cmd_start  # kech import — aylanma importdan saqlanish
    await cmd_start(m, state, bot)


@router.message(Command("admin"))
async def cmd_admin(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👨‍💻 <b>Admin panel</b>", reply_markup=panel_kb(m.from_user.id))


@router.callback_query(F.data == "adm:menu")
async def cb_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await safe_edit(call, "👨‍💻 <b>Admin panel</b>", panel_kb(call.from_user.id))


# ---------------- Drama qo'shish ----------------
@router.callback_query(F.data == "adm:add")
async def add_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddDrama.title)
    await call.answer()
    await safe_edit(call, "🎬 Drama <b>nomini</b> yuboring:", cancel_kb())


@router.message(AddDrama.title, F.text)
async def add_title(m: Message, state: FSMContext):
    await state.update_data(title=m.text.strip())
    await state.set_state(AddDrama.year)
    await m.answer("📅 Drama <b>yilini</b> yuboring (masalan: 2023):", reply_markup=cancel_kb())


@router.message(AddDrama.year, F.text)
async def add_year(m: Message, state: FSMContext):
    txt = m.text.strip()
    if not (txt.isdigit() and 1900 <= int(txt) <= 2100):
        await m.answer("⚠️ Yil noto'g'ri. 1900–2100 oralig'ida raqam yuboring:")
        return
    await state.update_data(year=int(txt))
    await state.set_state(AddDrama.genre)
    await m.answer("🎭 <b>Janrni</b> tanlang:", reply_markup=genre_kb("adm:ag"))


@router.callback_query(AddDrama.genre, F.data.startswith("adm:ag:"))
async def add_genre(call: CallbackQuery, state: FSMContext):
    genre = call.data.split(":")[2]
    if genre not in GENRE_UZ:
        await call.answer()
        return
    await state.update_data(genre=genre)
    await state.set_state(AddDrama.description)
    await call.answer()
    await safe_edit(call, "📄 Drama <b>tavsifini</b> yuboring (kerak bo'lmasa «-» yuboring):", cancel_kb())


@router.message(AddDrama.description, F.text)
async def add_desc(m: Message, state: FSMContext):
    desc = "" if m.text.strip() == "-" else m.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddDrama.poster)
    await m.answer("🖼 Drama <b>posterini</b> (rasm) yuboring:", reply_markup=cancel_kb())


@router.message(AddDrama.poster, F.photo)
async def add_poster(m: Message, state: FSMContext):
    data = await state.get_data()
    try:
        code = await db.add_drama(
            data["title"], data["year"], data["genre"], data["description"], m.photo[-1].file_id
        )
    except Exception as e:
        logging.exception("Drama qo'shishda xato")
        await m.answer(f"⚠️ Xatolik: {html.escape(str(e))}", reply_markup=back_kb())
        return
    await state.clear()
    await m.answer(
        f"✅ Drama qo'shildi!\n\n🎬 <b>{html.escape(data['title'])}</b>\n🔑 Kodi: <code>{code}</code>\n\n"
        "Endi «🎞 Qism qo'shish» orqali videolarni yuklang.",
        reply_markup=back_kb(),
    )


@router.message(AddDrama.poster)
async def add_poster_wrong(m: Message):
    await m.answer("⚠️ Iltimos, rasm (photo) yuboring.")


# ---------------- Qism qo'shish ----------------
@router.callback_query(F.data == "adm:addep")
async def addep_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddEp.code)
    await call.answer()
    await safe_edit(call, "🔑 Qism qo'shiladigan <b>drama kodini</b> yuboring:", cancel_kb())


@router.message(AddEp.code, F.text)
async def addep_code(m: Message, state: FSMContext):
    d = await db.get_drama_by_code(m.text.strip())
    if not d:
        await m.answer("❌ Bunday kodli drama topilmadi. Qaytadan yuboring:", reply_markup=cancel_kb())
        return
    nums = await db.episode_numbers(d["id"])
    await state.update_data(drama_id=d["id"])
    await state.set_state(AddEp.upload)
    await m.answer(
        f"🎬 {drama_line(d)}\n📺 Hozirgi qismlar soni: <b>{len(nums)}</b>\n\n"
        "🎞 Videolarni ketma-ket yuboring — har biri keyingi raqam bilan avtomatik qo'shiladi.\n"
        "Tugatgach «✅ Tugatish» tugmasini bosing.",
        reply_markup=kb([[btn("✅ Tugatish", "adm:menu", style="success")]]),
    )


@router.message(AddEp.upload, F.video)
async def addep_video(m: Message, state: FSMContext):
    data = await state.get_data()
    try:
        n = await db.add_episode(data["drama_id"], m.video.file_id)
    except Exception as e:
        logging.exception("Qism qo'shishda xato")
        await m.answer(f"⚠️ Xatolik: {html.escape(str(e))}")
        return
    await m.answer(f"✅ {n}-qism qo'shildi.")


@router.message(AddEp.upload)
async def addep_wrong(m: Message):
    await m.answer("⚠️ Iltimos, video yuboring (fayl sifatida emas, oddiy video).")


# ---------------- Drama o'chirish ----------------
@router.callback_query(F.data == "adm:deldrama")
async def deldrama_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(DelDrama.code)
    await call.answer()
    await safe_edit(call, "🔑 O'chiriladigan <b>drama kodini</b> yuboring:", cancel_kb())


@router.message(DelDrama.code, F.text)
async def deldrama_code(m: Message, state: FSMContext):
    d = await db.get_drama_by_code(m.text.strip())
    if not d:
        await m.answer("❌ Bunday kodli drama topilmadi. Qaytadan yuboring:", reply_markup=cancel_kb())
        return
    await m.answer(
        f"⚠️ {drama_line(d)} o'chirilsinmi?\nBarcha qismlari va sevimlilardagi yozuvlari ham o'chadi.",
        reply_markup=kb([[
            btn("🗑 Ha, o'chirish", f"adm:ddy:{d['id']}", style="danger"),
            btn("❌ Yo'q", "adm:menu", style="primary"),
        ]]),
    )


@router.callback_query(F.data.startswith("adm:ddy:"))
async def deldrama_confirm(call: CallbackQuery, state: FSMContext):
    try:
        did = int(call.data.split(":")[2])
        await db.delete_drama(did)
    except Exception as e:
        logging.exception("Drama o'chirishda xato")
        await call.answer(f"Xatolik: {e}", show_alert=True)
        return
    await state.clear()
    await call.answer("✅ O'chirildi")
    await safe_edit(call, "✅ Drama o'chirildi.", back_kb())


# ---------------- Qism o'chirish ----------------
@router.callback_query(F.data == "adm:delep")
async def delep_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(DelEp.code)
    await call.answer()
    await safe_edit(call, "🔑 Qismi o'chiriladigan <b>drama kodini</b> yuboring:", cancel_kb())


@router.message(DelEp.code, F.text)
async def delep_code(m: Message, state: FSMContext):
    d = await db.get_drama_by_code(m.text.strip())
    if not d:
        await m.answer("❌ Bunday kodli drama topilmadi. Qaytadan yuboring:", reply_markup=cancel_kb())
        return
    nums = await db.episode_numbers(d["id"])
    if not nums:
        await state.clear()
        await m.answer("📭 Bu dramada qismlar yo'q.", reply_markup=back_kb())
        return
    await state.update_data(drama_id=d["id"])
    await state.set_state(DelEp.number)
    await m.answer(
        f"🎬 {drama_line(d)}\n📺 Mavjud qismlar: <code>{', '.join(map(str, nums))}</code>\n\n"
        "O'chiriladigan <b>qism raqamini</b> yuboring:",
        reply_markup=cancel_kb(),
    )


@router.message(DelEp.number, F.text)
async def delep_number(m: Message, state: FSMContext):
    txt = m.text.strip()
    if not txt.isdigit():
        await m.answer("⚠️ Qism raqamini yuboring (faqat son):")
        return
    data = await state.get_data()
    try:
        ok = await db.delete_episode(data["drama_id"], int(txt))
    except Exception as e:
        logging.exception("Qism o'chirishda xato")
        await m.answer(f"⚠️ Xatolik: {html.escape(str(e))}", reply_markup=back_kb())
        return
    if not ok:
        await m.answer("❌ Bunday qism topilmadi. Boshqa raqam yuboring:")
        return
    await state.clear()
    await m.answer(f"✅ {txt}-qism o'chirildi.", reply_markup=back_kb())


# ---------------- Dramani tahrirlash ----------------
@router.callback_query(F.data == "adm:edit")
async def edit_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EditDrama.code)
    await call.answer()
    await safe_edit(call, "🔑 Tahrirlanadigan <b>drama kodini</b> yuboring:", cancel_kb())


@router.message(EditDrama.code, F.text)
async def edit_code(m: Message, state: FSMContext):
    d = await db.get_drama_by_code(m.text.strip())
    if not d:
        await m.answer("❌ Bunday kodli drama topilmadi. Qaytadan yuboring:", reply_markup=cancel_kb())
        return
    await state.update_data(drama_id=d["id"])
    await state.set_state(EditDrama.field)
    rows = [[btn(label, f"adm:ef:{key}", style="primary")] for key, label in EDIT_FIELDS.items()]
    rows.append([btn("❌ Bekor qilish", "adm:menu", style="danger")])
    await m.answer(f"✏️ {drama_line(d)}\n\nQaysi maydonni o'zgartiramiz?", reply_markup=kb(rows))


@router.callback_query(EditDrama.field, F.data.startswith("adm:ef:"))
async def edit_field(call: CallbackQuery, state: FSMContext):
    field = call.data.split(":")[2]
    if field not in EDIT_FIELDS:
        await call.answer()
        return
    await state.update_data(field=field)
    await state.set_state(EditDrama.value)
    await call.answer()
    if field == "genre":
        await safe_edit(call, "🎭 Yangi <b>janrni</b> tanlang:", genre_kb("adm:eg"))
    elif field == "poster":
        await safe_edit(call, "🖼 Yangi <b>posterni</b> (rasm) yuboring:", cancel_kb())
    elif field == "description":
        await safe_edit(call, "📄 Yangi <b>tavsifni</b> yuboring («-» — bo'sh qoldirish):", cancel_kb())
    else:
        await safe_edit(call, f"{EDIT_FIELDS[field]} — yangi qiymatni yuboring:", cancel_kb())


@router.callback_query(EditDrama.value, F.data.startswith("adm:eg:"))
async def edit_genre(call: CallbackQuery, state: FSMContext):
    genre = call.data.split(":")[2]
    data = await state.get_data()
    if genre not in GENRE_UZ or data.get("field") != "genre":
        await call.answer()
        return
    await db.update_drama(data["drama_id"], "genre", genre)
    await state.clear()
    await call.answer("✅ Saqlandi")
    await safe_edit(call, "✅ Janr yangilandi.", back_kb())


@router.message(EditDrama.value, F.photo)
async def edit_poster(m: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("field") != "poster":
        await m.answer("⚠️ Bu maydon uchun rasm kerak emas.")
        return
    await db.update_drama(data["drama_id"], "poster", m.photo[-1].file_id)
    await state.clear()
    await m.answer("✅ Poster yangilandi.", reply_markup=back_kb())


@router.message(EditDrama.value, F.text)
async def edit_value(m: Message, state: FSMContext):
    data = await state.get_data()
    field, txt = data.get("field"), m.text.strip()
    if field == "poster":
        await m.answer("⚠️ Iltimos, rasm (photo) yuboring.")
        return
    if field == "genre":
        await m.answer("⚠️ Janrni yuqoridagi tugmalardan tanlang.")
        return
    if field == "year":
        if not (txt.isdigit() and 1900 <= int(txt) <= 2100):
            await m.answer("⚠️ Yil noto'g'ri. 1900–2100 oralig'ida raqam yuboring:")
            return
        value = int(txt)
    elif field == "description":
        value = "" if txt == "-" else txt
    else:
        value = txt
    try:
        await db.update_drama(data["drama_id"], field, value)
    except Exception as e:
        logging.exception("Tahrirlashda xato")
        await m.answer(f"⚠️ Xatolik: {html.escape(str(e))}", reply_markup=back_kb())
        return
    await state.clear()
    await m.answer("✅ Ma'lumot yangilandi.", reply_markup=back_kb())


# ---------------- Post qilish ----------------
def build_caption(d) -> str:
    """Tayyor caption: nomi, yili, kodi, asosiy kanal havolasi."""
    return (
        f"🎬 <b>{html.escape(d['title'])}</b>\n\n"
        f"📅 Yili: <b>{d['year']}</b>\n"
        f"🔑 Kodi: <code>{d['code']}</code>\n\n"
        f"📢 Asosiy kanal: {MAIN_CHANNEL_URL}"
    )


def post_kb():
    return kb([
        [btn("✅ Yuborish", "adm:pgo", style="success"),
         btn("✏️ Tahrirlash", "adm:pedit", style="primary")],
        [btn("❌ Bekor qilish", "adm:menu", style="danger")],
    ])


async def show_preview(msg: Message, state: FSMContext, d, caption: str | None = None):
    caption = caption or build_caption(d)
    await state.update_data(drama_id=d["id"], caption=caption)
    await state.set_state(PostSG.confirm)
    warn = "\n\n⚠️ Caption 1024 belgidan oshdi — qisqartiring!" if len(caption) > 1024 else ""
    await msg.answer_photo(d["poster"], caption=caption[:1024], reply_markup=post_kb())
    if warn:
        await msg.answer(warn.strip())


@router.callback_query(F.data == "adm:post")
async def post_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PostSG.query)
    await call.answer()
    await safe_edit(call, "📤 Post qilinadigan <b>drama nomi yoki kodini</b> yuboring:", cancel_kb())


@router.message(PostSG.query, F.text)
async def post_query(m: Message, state: FSMContext):
    q = m.text.strip()
    d = await db.get_drama_by_code(q)
    if d:
        await show_preview(m, state, d)
        return
    results = await db.search_title(q, limit=10)
    if not results:
        await m.answer("❌ Drama topilmadi. Qaytadan yuboring:", reply_markup=cancel_kb())
        return
    if len(results) == 1:
        await show_preview(m, state, results[0])
        return
    rows = [[btn(f"🎬 {r['title']} ({r['year']}) — {r['code']}", f"adm:pp:{r['id']}")] for r in results]
    rows.append([btn("❌ Bekor qilish", "adm:menu", style="danger")])
    await m.answer("🔎 Bir nechta natija topildi, tanlang:", reply_markup=kb(rows))


@router.callback_query(PostSG.query, F.data.startswith("adm:pp:"))
async def post_pick(call: CallbackQuery, state: FSMContext):
    d = await db.get_drama(int(call.data.split(":")[2]))
    if not d:
        await call.answer("❌ Topilmadi", show_alert=True)
        return
    await call.answer()
    await show_preview(call.message, state, d)


@router.callback_query(PostSG.confirm, F.data == "adm:pedit")
async def post_edit(call: CallbackQuery, state: FSMContext):
    await state.set_state(PostSG.edit)
    await call.answer()
    await call.message.answer(
        "✏️ Caption'ning <b>yangi matnini</b> yuboring.\n"
        "Hozirgi matnni nusxalab, o'zgartirib yuborishingiz mumkin (formatlash saqlanadi).",
        reply_markup=cancel_kb(),
    )


@router.message(PostSG.edit, F.text)
async def post_edit_text(m: Message, state: FSMContext):
    data = await state.get_data()
    d = await db.get_drama(data["drama_id"])
    if not d:
        await state.clear()
        await m.answer("❌ Drama topilmadi.", reply_markup=back_kb())
        return
    await show_preview(m, state, d, caption=m.html_text)


@router.callback_query(PostSG.confirm, F.data == "adm:pgo")
async def post_choose_channel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if len(data.get("caption", "")) > 1024:
        await call.answer("⚠️ Caption 1024 belgidan oshdi. Tahrirlab qisqartiring.", show_alert=True)
        return
    channels = await db.get_channels("post")
    if not channels:
        await call.answer("⚠️ Post kanallari yo'q. Owner kanal qo'shishi kerak.", show_alert=True)
        return
    await call.answer()
    rows = [[btn(f"📣 {c['title']}", f"adm:ps:{c['id']}", style="success")] for c in channels]
    rows.append([btn("❌ Bekor qilish", "adm:menu", style="danger")])
    await call.message.answer("📣 Qaysi kanalga yuboramiz?", reply_markup=kb(rows))


@router.callback_query(PostSG.confirm, F.data.startswith("adm:ps:"))
async def post_send(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ch = await db.get_channel(int(call.data.split(":")[2]))
    d = await db.get_drama(data.get("drama_id", 0))
    if not ch or not d:
        await call.answer("❌ Kanal yoki drama topilmadi", show_alert=True)
        return
    try:
        # Kanal posti uchun protect_content o'chiriladi
        await bot.send_photo(
            ch["chat_id"], d["poster"], caption=data["caption"], protect_content=False
        )
    except TelegramAPIError as e:
        logging.error("Post yuborishda xato: %s", e)
        await call.answer()
        await call.message.answer(
            f"❌ Yuborib bo'lmadi: <code>{html.escape(str(e))}</code>\n"
            "Bot kanalda admin ekanini va caption to'g'riligini tekshiring.",
            reply_markup=back_kb(),
        )
        return
    await state.clear()
    await call.answer("✅ Yuborildi")
    await call.message.answer(f"✅ Post «{html.escape(ch['title'])}» kanaliga yuborildi.", reply_markup=back_kb())
