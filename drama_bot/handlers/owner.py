"""Owner paneli: majburiy obuna / post kanallari va adminlarni boshqarish."""
import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, MessageOriginChannel, MessageOriginUser

from database import db
from keyboards import btn, kb
from states import AdminSG, ChannelSG
from utils import ADMIN_IDS, IsOwner, load_admins, safe_edit

CANCEL_NOTE = "ℹ️ Jarayon bekor qilindi. /admin — admin panel, /start — bosh menyu."

router = Router(name="owner")
router.message.filter(IsOwner())
router.callback_query.filter(IsOwner())

KIND_TITLE = {"sub": "📢 Majburiy obuna kanallari", "post": "📣 Post kanallari"}


def back_kb():
    return kb([[btn("⬅️ Admin panel", "adm:menu")]])


def cancel_kb():
    return kb([[btn("❌ Bekor qilish", "adm:menu", style="danger")]])


# ---------------- Kanallar ----------------
async def show_channels(call: CallbackQuery, kind: str):
    channels = await db.get_channels(kind)
    rows = [[btn(f"🗑 {c['title']}", f"own:chdel:{c['id']}:{kind}", style="danger")] for c in channels]
    rows.append([btn("➕ Kanal qo'shish", f"own:chadd:{kind}", style="success")])
    rows.append([btn("⬅️ Admin panel", "adm:menu")])
    text = f"<b>{KIND_TITLE[kind]}</b>\n\n"
    text += "O'chirish uchun kanal nomini bosing:" if channels else "Hozircha kanallar yo'q."
    await safe_edit(call, text, kb(rows))


@router.callback_query(F.data.startswith("own:ch:"))
async def channels_list(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[2]
    if kind not in KIND_TITLE:
        await call.answer()
        return
    await state.clear()
    await call.answer()
    await show_channels(call, kind)


@router.callback_query(F.data.startswith("own:chdel:"))
async def channel_delete(call: CallbackQuery):
    _, _, ch_id, kind = call.data.split(":")
    await db.del_channel(int(ch_id))
    await call.answer("🗑 O'chirildi")
    await show_channels(call, kind)


@router.callback_query(F.data.startswith("own:chadd:"))
async def channel_add_start(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[2]
    if kind not in KIND_TITLE:
        await call.answer()
        return
    await state.set_state(ChannelSG.add)
    await state.update_data(kind=kind)
    await call.answer()
    await safe_edit(
        call,
        "📎 Kanalni qo'shish uchun quyidagilardan birini yuboring:\n"
        "• kanaldan biror xabarni <b>forward</b> qiling\n"
        "• yoki kanal <b>@username</b> yoki <b>ID</b> (-100...) sini yuboring\n\n"
        "⚠️ Bot avval kanalga <b>admin</b> qilib qo'shilgan bo'lishi shart.",
        cancel_kb(),
    )


@router.message(ChannelSG.add)
async def channel_add(m: Message, state: FSMContext, bot: Bot):
    if m.text and m.text.startswith("/"):  # buyruq — jarayonni bekor qilamiz
        await state.clear()
        await m.answer(CANCEL_NOTE)
        return
    data = await state.get_data()
    kind = data["kind"]
    # Kanalni aniqlash
    if isinstance(m.forward_origin, MessageOriginChannel):
        ref = m.forward_origin.chat.id
    elif m.text:
        ref = m.text.strip()
        if ref.lstrip("-").isdigit():
            ref = int(ref)
        elif not ref.startswith("@"):
            ref = "@" + ref
    else:
        await m.answer("⚠️ Forward xabar, @username yoki ID yuboring.")
        return
    try:
        chat = await bot.get_chat(ref)
        me = await bot.get_chat_member(chat.id, bot.id)
        if me.status not in ("administrator", "creator"):
            await m.answer("❌ Bot bu kanalda admin emas. Avval botni admin qiling.", reply_markup=cancel_kb())
            return
        if chat.username:
            url = f"https://t.me/{chat.username}"
        else:
            url = (await bot.create_chat_invite_link(chat.id)).invite_link
    except TelegramAPIError as e:
        logging.warning("Kanal qo'shishda xato: %s", e)
        await m.answer(
            f"❌ Kanal topilmadi yoki ruxsat yo'q:\n<code>{html.escape(str(e))}</code>",
            reply_markup=cancel_kb(),
        )
        return
    added = await db.add_channel(chat.id, chat.title or str(chat.id), url, kind)
    await state.clear()
    if added:
        await m.answer(f"✅ Kanal qo'shildi: <b>{html.escape(chat.title or '')}</b>", reply_markup=back_kb())
    else:
        await m.answer("ℹ️ Bu kanal allaqachon ro'yxatda bor.", reply_markup=back_kb())


# ---------------- Adminlar ----------------
async def show_admins(call: CallbackQuery):
    ids = sorted(ADMIN_IDS)
    rows = [[btn(f"🗑 {uid}", f"own:admdel:{uid}", style="danger")] for uid in ids]
    rows.append([btn("➕ Admin tayinlash", "own:admadd", style="success")])
    rows.append([btn("⬅️ Admin panel", "adm:menu")])
    text = "<b>👮 Adminlar</b>\n\n" + ("Olib tashlash uchun ID ni bosing:" if ids else "Hozircha adminlar yo'q.")
    await safe_edit(call, text, kb(rows))


@router.callback_query(F.data == "own:adm")
async def admins_list(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await show_admins(call)


@router.callback_query(F.data.startswith("own:admdel:"))
async def admin_remove(call: CallbackQuery):
    await db.del_admin(int(call.data.split(":")[2]))
    await load_admins()
    await call.answer("🗑 Admin olib tashlandi")
    await show_admins(call)


@router.callback_query(F.data == "own:admadd")
async def admin_add_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminSG.add)
    await call.answer()
    await safe_edit(
        call,
        "👤 Yangi adminning <b>Telegram ID</b> sini yuboring yoki uning biror xabarini forward qiling:",
        cancel_kb(),
    )


@router.message(AdminSG.add)
async def admin_add(m: Message, state: FSMContext):
    if m.text and m.text.startswith("/"):
        await state.clear()
        await m.answer(CANCEL_NOTE)
        return
    uid = None
    if isinstance(m.forward_origin, MessageOriginUser):
        uid = m.forward_origin.sender_user.id
    elif m.text and m.text.strip().isdigit():
        uid = int(m.text.strip())
    if uid is None:
        await m.answer("⚠️ Raqamli ID yuboring yoki foydalanuvchi xabarini forward qiling.")
        return
    await db.add_admin(uid)
    await load_admins()
    await state.clear()
    await m.answer(f"✅ <code>{uid}</code> admin qilib tayinlandi.", reply_markup=back_kb())
