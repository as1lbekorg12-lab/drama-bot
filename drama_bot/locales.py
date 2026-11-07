"""Uch tildagi (uz / ru / en) matnlar. Kalitlar uchala tilda bir xil."""

CHOOSE_LANG = "🌐 Tilni tanlang / Выберите язык / Choose language:"

UZ = {
    "sub_required": "📢 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling</b>, so'ng «✅ Tekshirish» tugmasini bosing:",
    "btn_check": "✅ Tekshirish",
    "sub_still": "❌ Siz hali barcha kanallarga obuna bo'lmagansiz!",
    "menu": "🎬 <b>Asosiy menyu</b>\n\nKerakli bo'limni tanlang:",
    "btn_code": "🔢 Kod bo'yicha qidirish",
    "btn_name": "🔍 Nom bo'yicha qidirish",
    "btn_genre": "🎭 Janr bo'yicha",
    "btn_fav": "❤️ Sevimlilar",
    "btn_home": "🏠 Bosh menyu",
    "ask_code": "🔢 Drama kodini yuboring:",
    "ask_name": "🔍 Drama nomini yuboring:",
    "not_found": "😔 Hech narsa topilmadi. Qaytadan urinib ko'ring.",
    "results": "🔎 <b>Qidiruv natijalari:</b>",
    "genre_pick": "🎭 Janrni tanlang:",
    "genre_action": "⚔️ Jangari",
    "genre_romance": "💕 Romantik",
    "genre_list": "🎭 <b>{genre}</b> dramalari:",
    "empty_list": "😔 Hozircha dramalar yo'q.",
    "fav_title": "❤️ <b>Sevimli dramalaringiz:</b>",
    "fav_empty": "💔 Sevimlilar ro'yxati bo'sh.",
    "fav_add": "🤍 Sevimlilarga qo'shish",
    "fav_remove": "💔 Sevimlilardan olib tashlash",
    "fav_added": "❤️ Sevimlilarga qo'shildi!",
    "fav_removed": "💔 Sevimlilardan olib tashlandi.",
    "card": "🎬 <b>{title}</b>\n\n📅 Yili: <b>{year}</b>\n🎭 Janr: <b>{genre}</b>\n🔑 Kodi: <code>{code}</code>\n📺 Qismlar soni: <b>{count}</b>\n\n{desc}",
    "no_eps": "📭 Bu dramaga hali qismlar qo'shilmagan.",
    "ep_caption": "🎬 <b>{title}</b>\n📺 {n}-qism",
    "ep_missing": "❌ Qism topilmadi.",
    "text_only": "✍️ Iltimos, matn yuboring.",
    "error": "⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
}

RU = {
    "sub_required": "📢 <b>Чтобы пользоваться ботом, подпишитесь на каналы ниже</b>, затем нажмите «✅ Проверить»:",
    "btn_check": "✅ Проверить",
    "sub_still": "❌ Вы ещё не подписались на все каналы!",
    "menu": "🎬 <b>Главное меню</b>\n\nВыберите нужный раздел:",
    "btn_code": "🔢 Поиск по коду",
    "btn_name": "🔍 Поиск по названию",
    "btn_genre": "🎭 По жанру",
    "btn_fav": "❤️ Избранное",
    "btn_home": "🏠 Главное меню",
    "ask_code": "🔢 Отправьте код дорамы:",
    "ask_name": "🔍 Отправьте название дорамы:",
    "not_found": "😔 Ничего не найдено. Попробуйте ещё раз.",
    "results": "🔎 <b>Результаты поиска:</b>",
    "genre_pick": "🎭 Выберите жанр:",
    "genre_action": "⚔️ Боевик",
    "genre_romance": "💕 Романтика",
    "genre_list": "🎭 Дорамы жанра <b>{genre}</b>:",
    "empty_list": "😔 Пока дорам нет.",
    "fav_title": "❤️ <b>Ваши избранные дорамы:</b>",
    "fav_empty": "💔 Список избранного пуст.",
    "fav_add": "🤍 В избранное",
    "fav_remove": "💔 Убрать из избранного",
    "fav_added": "❤️ Добавлено в избранное!",
    "fav_removed": "💔 Удалено из избранного.",
    "card": "🎬 <b>{title}</b>\n\n📅 Год: <b>{year}</b>\n🎭 Жанр: <b>{genre}</b>\n🔑 Код: <code>{code}</code>\n📺 Количество серий: <b>{count}</b>\n\n{desc}",
    "no_eps": "📭 К этой дораме ещё не добавлены серии.",
    "ep_caption": "🎬 <b>{title}</b>\n📺 Серия {n}",
    "ep_missing": "❌ Серия не найдена.",
    "text_only": "✍️ Пожалуйста, отправьте текст.",
    "error": "⚠️ Произошла ошибка. Попробуйте ещё раз.",
}

EN = {
    "sub_required": "📢 <b>To use the bot, subscribe to the channels below</b>, then press “✅ Check”:",
    "btn_check": "✅ Check",
    "sub_still": "❌ You haven't subscribed to all channels yet!",
    "menu": "🎬 <b>Main menu</b>\n\nChoose a section:",
    "btn_code": "🔢 Search by code",
    "btn_name": "🔍 Search by title",
    "btn_genre": "🎭 By genre",
    "btn_fav": "❤️ Favorites",
    "btn_home": "🏠 Main menu",
    "ask_code": "🔢 Send the drama code:",
    "ask_name": "🔍 Send the drama title:",
    "not_found": "😔 Nothing found. Please try again.",
    "results": "🔎 <b>Search results:</b>",
    "genre_pick": "🎭 Choose a genre:",
    "genre_action": "⚔️ Action",
    "genre_romance": "💕 Romance",
    "genre_list": "🎭 <b>{genre}</b> dramas:",
    "empty_list": "😔 No dramas yet.",
    "fav_title": "❤️ <b>Your favorite dramas:</b>",
    "fav_empty": "💔 Your favorites list is empty.",
    "fav_add": "🤍 Add to favorites",
    "fav_remove": "💔 Remove from favorites",
    "fav_added": "❤️ Added to favorites!",
    "fav_removed": "💔 Removed from favorites.",
    "card": "🎬 <b>{title}</b>\n\n📅 Year: <b>{year}</b>\n🎭 Genre: <b>{genre}</b>\n🔑 Code: <code>{code}</code>\n📺 Episodes: <b>{count}</b>\n\n{desc}",
    "no_eps": "📭 No episodes have been added to this drama yet.",
    "ep_caption": "🎬 <b>{title}</b>\n📺 Episode {n}",
    "ep_missing": "❌ Episode not found.",
    "text_only": "✍️ Please send text.",
    "error": "⚠️ Something went wrong. Please try again.",
}

TEXTS = {"uz": UZ, "ru": RU, "en": EN}
LANGS = ("uz", "ru", "en")


def tr(lang, key: str, **kw) -> str:
    """Tanlangan tildagi matnni qaytaradi (til noma'lum bo'lsa — o'zbekcha)."""
    data = TEXTS.get(lang or "uz", UZ)
    text = data[key]
    return text.format(**kw) if kw else text


def tr_or_all(lang, key: str, sep: str = "\n\n") -> str:
    """Til hali tanlanmagan bo'lsa — uchala tildagi matnni birlashtiradi."""
    if lang in TEXTS:
        return TEXTS[lang][key]
    return sep.join(TEXTS[l][key] for l in LANGS)


# Import vaqtida tillar mosligini tekshirish
assert set(UZ) == set(RU) == set(EN), "Til kalitlari mos emas!"
