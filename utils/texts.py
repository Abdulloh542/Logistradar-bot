T = {
    "uz": {
        "welcome": (
            "📦 <b>Logistradar Bot</b>ga xush kelibsiz!\n\n"
            "🚛 O'zbekiston bo'yicha yuk va transport qidirish platformasi.\n"
            "300+ logistika guruhidan e'lonlarni to'playdi.\n\n"
            "Quyidagi tugmalardan birini tanlang:"
        ),
        "search_hint": (
            "🔍 <b>Tezkor Qidiruv</b>\n\n"
            "Yuklarni topish uchun jo'nash va yetib borish shahar yoki mamlakatni kiriting.\n\n"
            "<b>Misollar:</b>\n"
            "• <code>Toshkent</code>\n"
            "• <code>Toshkent Samarqand</code>\n"
            "• <code>Toshkent Moskva</code>\n"
            "• <code>Buxoro Qozog'iston</code>"
        ),
        "find_truck_msg": (
            "🚛 <b>Moshina topish</b>\n\n"
            "Mamlakatni tanlang:"
        ),
        "find_cargo_msg": (
            "📦 <b>Yuk topish</b>\n\n"
            "Yo'nalishni tanlang:"
        ),
        "truck_select": "🚗 <b>Avto turini tanlang:</b>",
        "truck_selected": "✅ Tanlangan avto turi: <b>{truck}</b>\n\nEndi shaharlarni kiriting:",
        "no_results": "🔍 Natija topilmadi. Umumiy e'lonlar ko'rsatilmoqda:",
        "results_header": "🚛 <b>{count}</b> ta e'lon topildi, <b>{today}</b> tasi bugungi",
        "ad_card": (
            "<b>{n}. {ff}{from_loc} → {ft}{to_loc}</b>\n"
            "{weight_line}"
            "{truck_line}"
            "{cargo_line}"
            "{price_line}"
            "🛣 {km} km · {h} soatlik\n"
            "⏱ {ago} min oldin · 📡 {src}"
        ),
        "ad_detail": (
            "📋 <b>Batafsil ma'lumot</b>\n\n"
            "🗺 <b>Yo'nalish:</b> {ff}{from_loc} → {ft}{to_loc}\n"
            "{weight_line}"
            "{truck_line}"
            "{cargo_line}"
            "{price_line}"
            "🛣 <b>Masofa:</b> {km} km\n"
            "⏱ <b>Vaqt:</b> {h} soatlik\n"
            "{customs_line}"
            "📡 <b>Manba:</b> {src}\n"
        ),
        "phone_reveal": "📞 Telefon: <code>{phone}</code>\n\nNusxalash uchun raqamga bosing.",
        "no_phone": "📞 Telefon raqam mavjud emas.",
        "post_steps": [
            "📍 <b>Qadam 1/7</b> — Jo'nab ketadigan shahar yoki hudud:\n\nMisol: <code>Toshkent</code>",
            "📍 <b>Qadam 2/7</b> — Boradigan shahar yoki hudud:\n\nMisol: <code>Samarqand</code>",
            "⚖️ <b>Qadam 3/7</b> — Yuk og'irligi:\n\nMisol: <code>20t</code>",
            "🚚 <b>Qadam 4/7</b> — Transport turini tanlang:",
            "📦 <b>Qadam 5/7</b> — Yuk nomi:\n\nMisol: <code>Meva, qurilish materiallari</code>",
            "💰 <b>Qadam 6/7</b> — Narx:\n\nMisol: <code>500 USD</code> yoki <code>kelishiladi</code>",
            "📞 <b>Qadam 7/7</b> — Telefon raqam:\n\nMisol: <code>+998901234567</code>",
        ],
        "post_confirm": (
            "✅ <b>E'loningiz qabul qilindi!</b>\n\n"
            "🚛 {from_loc} → {to_loc}\n"
            "⚖️ {weight} | 🚚 {truck}\n"
            "📦 {cargo} | 💰 {price}\n"
            "📞 {phone}\n\n"
            "📢 Barcha ulangan guruhlarga tarqatildi!"
        ),
        "my_ads_empty": (
            "📋 <b>Sizda hali e'lon yo'q.</b>\n\n"
            "E'lon qo'shish uchun «📢 E'lon qo'shish» tugmasini bosing."
        ),
        "my_ads_header": "📋 <b>Sizning e'lonlaringiz ({count} ta):</b>",
        "my_ad_item": (
            "🚛 <b>{from_loc} → {to_loc}</b>\n"
            "⚖️ {weight} | 🚚 {truck}\n"
            "📦 {cargo} | 💰 {price}\n"
            "📞 {phone}\n"
            "📅 {created}"
        ),
        "delete_confirm": "🗑 <b>O'chirishni tasdiqlaysizmi?</b>",
        "deleted": "✅ E'lon o'chirildi.",
        "delete_cancel": "❌ Bekor qilindi.",
        "settings": (
            "⚙️ <b>Sozlamalar</b>\n\n"
            "🌐 Til: {lang}\n"
            "🚗 Avto turi: {truck}\n\n"
            "Tilni tanlang:"
        ),
        "lang_set": "✅ Til o'zgartirildi: 🇺🇿 O'zbek",
        "cancelled": "❌ Bekor qilindi. Asosiy menyu:",
        "load_more": "📋 Ko'proq ko'rsatish ({from}-{to} / {total})",
        "no_more": "✅ Barcha e'lonlar ko'rsatildi.",
    },
    "ru": {
        "welcome": (
            "📦 <b>Добро пожаловать в Logistradar Bot!</b>\n\n"
            "🚛 Платформа поиска грузов и транспорта по Узбекистану.\n"
            "Собирает объявления из 300+ логистических групп.\n\n"
            "Выберите одну из кнопок:"
        ),
        "search_hint": (
            "🔍 <b>Быстрый поиск</b>\n\n"
            "Введите город или страну отправки и назначения.\n\n"
            "<b>Примеры:</b>\n"
            "• <code>Ташкент</code>\n"
            "• <code>Ташкент Самарканд</code>\n"
            "• <code>Ташкент Москва</code>\n"
            "• <code>Бухара Казахстан</code>"
        ),
        "find_truck_msg": "🚛 <b>Найти машину</b>\n\nВыберите страну:",
        "find_cargo_msg": "📦 <b>Найти груз</b>\n\nВыберите направление:",
        "truck_select": "🚗 <b>Выберите тип авто:</b>",
        "truck_selected": "✅ Выбранный тип авто: <b>{truck}</b>\n\nТеперь введите города:",
        "no_results": "🔍 Ничего не найдено. Показываем все объявления:",
        "results_header": "🚛 Найдено <b>{count}</b> объявлений, <b>{today}</b> сегодня",
        "ad_card": (
            "<b>{n}. {ff}{from_loc} → {ft}{to_loc}</b>\n"
            "{weight_line}"
            "{truck_line}"
            "{cargo_line}"
            "{price_line}"
            "🛣 {km} км · {h} часов\n"
            "⏱ {ago} мин назад · 📡 {src}"
        ),
        "ad_detail": (
            "📋 <b>Подробная информация</b>\n\n"
            "🗺 <b>Направление:</b> {ff}{from_loc} → {ft}{to_loc}\n"
            "{weight_line}"
            "{truck_line}"
            "{cargo_line}"
            "{price_line}"
            "🛣 <b>Расстояние:</b> {km} км\n"
            "⏱ <b>Время:</b> {h} часов\n"
            "{customs_line}"
            "📡 <b>Источник:</b> {src}\n"
        ),
        "phone_reveal": "📞 Телефон: <code>{phone}</code>\n\nНажмите на номер чтобы скопировать.",
        "no_phone": "📞 Номер телефона недоступен.",
        "post_steps": [
            "📍 <b>Шаг 1/7</b> — Город или регион отправки:\n\nПример: <code>Ташкент</code>",
            "📍 <b>Шаг 2/7</b> — Город или регион назначения:\n\nПример: <code>Самарканд</code>",
            "⚖️ <b>Шаг 3/7</b> — Вес груза:\n\nПример: <code>20т</code>",
            "🚚 <b>Шаг 4/7</b> — Выберите тип транспорта:",
            "📦 <b>Шаг 5/7</b> — Название груза:\n\nПример: <code>Фрукты, стройматериалы</code>",
            "💰 <b>Шаг 6/7</b> — Цена:\n\nПример: <code>500 USD</code> или <code>договорная</code>",
            "📞 <b>Шаг 7/7</b> — Номер телефона:\n\nПример: <code>+998901234567</code>",
        ],
        "post_confirm": (
            "✅ <b>Объявление принято!</b>\n\n"
            "🚛 {from_loc} → {to_loc}\n"
            "⚖️ {weight} | 🚚 {truck}\n"
            "📦 {cargo} | 💰 {price}\n"
            "📞 {phone}\n\n"
            "📢 Разослано по всем группам!"
        ),
        "my_ads_empty": (
            "📋 <b>У вас ещё нет объявлений.</b>\n\n"
            "Нажмите «📢 Добавить объявление» чтобы создать."
        ),
        "my_ads_header": "📋 <b>Ваши объявления ({count} шт.):</b>",
        "my_ad_item": (
            "🚛 <b>{from_loc} → {to_loc}</b>\n"
            "⚖️ {weight} | 🚚 {truck}\n"
            "📦 {cargo} | 💰 {price}\n"
            "📞 {phone}\n"
            "📅 {created}"
        ),
        "delete_confirm": "🗑 <b>Подтвердить удаление?</b>",
        "deleted": "✅ Объявление удалено.",
        "delete_cancel": "❌ Отменено.",
        "settings": (
            "⚙️ <b>Настройки</b>\n\n"
            "🌐 Язык: {lang}\n"
            "🚗 Тип авто: {truck}\n\n"
            "Выберите язык:"
        ),
        "lang_set": "✅ Язык изменён: 🇷🇺 Русский",
        "cancelled": "❌ Отменено. Главное меню:",
        "load_more": "📋 Показать ещё ({from}-{to} / {total})",
        "no_more": "✅ Все объявления показаны.",
    }
}

FLAGS = {
    "O'zbekiston": "🇺🇿", "Россия": "🇷🇺", "Rossiya": "🇷🇺",
    "Qozog'iston": "🇰🇿", "Казахстан": "🇰🇿",
    "Qirg'iziston": "🇰🇬", "Bishkek": "🇰🇬",
    "Turkiya": "🇹🇷", "Stambul": "🇹🇷",
    "Germaniya": "🇩🇪", "Gruziya": "🇬🇪",
    "Belarus": "🇧🇾", "Ozarbayjon": "🇦🇿", "Baku": "🇦🇿",
    "Tojikiston": "🇹🇯", "Afg'oniston": "🇦🇫",
    "Toshkent": "🇺🇿", "Samarqand": "🇺🇿", "Buxoro": "🇺🇿",
    "Namangan": "🇺🇿", "Andijon": "🇺🇿", "Farg'ona": "🇺🇿",
    "Nukus": "🇺🇿", "Termiz": "🇺🇿", "Urganch": "🇺🇿",
    "Moskva": "🇷🇺", "Moskva": "🇷🇺",
}

def get_flag(city: str) -> str:
    for k, v in FLAGS.items():
        if k.lower() in city.lower():
            return v
    return "🏳"

def txt(key: str, lang: str, **kwargs) -> str:
    val = T.get(lang, T["uz"]).get(key, "")
    if kwargs:
        try:
            val = val.format(**kwargs)
        except Exception:
            pass
    return val

def format_ad_card(ad: dict, n: int, lang: str) -> str:
    ff = ad.get("ff") or get_flag(ad.get("from_loc", ""))
    ft = ad.get("ft") or get_flag(ad.get("to_loc", ""))
    w  = f"⚖️ {ad['weight']}\n" if ad.get("weight") else ""
    tr = f"🚚 {ad['truck']}\n" if ad.get("truck") else ""
    ca = f"📦 {ad['cargo']}\n" if ad.get("cargo") else ""
    pr = f"🤑 {ad['price']}\n" if ad.get("price") else ""
    ago = ad.get("ago") or "?"
    return txt("ad_card", lang,
        n=n, ff=ff, from_loc=ad.get("from_loc",""), ft=ft, to_loc=ad.get("to_loc",""),
        weight_line=w, truck_line=tr, cargo_line=ca, price_line=pr,
        km=ad.get("km",0), h=ad.get("hours",0), ago=ago, src=ad.get("source","—")
    )

def format_ad_detail(ad: dict, lang: str) -> str:
    ff = ad.get("ff") or get_flag(ad.get("from_loc", ""))
    ft = ad.get("ft") or get_flag(ad.get("to_loc", ""))
    lbl = {"uz": ("⚖️ <b>Og'irlik:</b> ", "🚚 <b>Transport:</b> ", "📦 <b>Yuk:</b> ", "💰 <b>Narx:</b> ", "🛃 <b>Bojxona:</b> "),
           "ru": ("⚖️ <b>Вес:</b> ", "🚚 <b>Транспорт:</b> ", "📦 <b>Груз:</b> ", "💰 <b>Цена:</b> ", "🛃 <b>Таможня:</b> ")}.get(lang, ("","","","",""))
    w  = f"{lbl[0]}{ad['weight']}\n" if ad.get("weight") else ""
    tr = f"{lbl[1]}{ad['truck']}\n"  if ad.get("truck") else ""
    ca = f"{lbl[2]}{ad['cargo']}\n"  if ad.get("cargo") else ""
    pr = f"{lbl[3]}{ad['price']}\n"  if ad.get("price") else ""
    cu = f"{lbl[4]}{ad['customs']}\n" if ad.get("customs") else ""
    return txt("ad_detail", lang,
        ff=ff, from_loc=ad.get("from_loc",""), ft=ft, to_loc=ad.get("to_loc",""),
        weight_line=w, truck_line=tr, cargo_line=ca, price_line=pr,
        km=ad.get("km",0), h=ad.get("hours",0), customs_line=cu, src=ad.get("source","—")
    )
