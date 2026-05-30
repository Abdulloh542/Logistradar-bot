from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from config import Config
from pathlib import Path as _P
import re as _re

def _get_webapp_url() -> str:
    """Always read fresh WEBAPP_URL from .env (tunnel URL changes on restart)."""
    try:
        env = (_P(__file__).parent.parent / ".env").read_text("utf-8")
        m = _re.search(r'WEBAPP_URL=(https?://\S+)', env)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return Config.WEBAPP_URL

def _build_webapp_url(user_id: int = 0, first_name: str = "", username: str = "", photo: str = "") -> str:
    """Build WebApp URL with user data as query params (fallback for initDataUnsafe)."""
    import urllib.parse
    base = _get_webapp_url()
    if not base:
        return base
    params = {}
    if user_id:
        params['uid'] = str(user_id)
    if first_name:
        params['fn'] = first_name
    if username:
        params['un'] = username
    if photo:
        params['ph'] = photo
    if params:
        return base + '?' + urllib.parse.urlencode(params)
    return base

TRUCKS = ["Hammasi", "Tent", "Ref", "Ref rejimsiz", "Izoterma",
          "Kichkina Isuzu", "Katta Isuzu", "Bortovoy", "Konteyner",
          "Chakman", "Kamaz", "Mega", "Ploshadka", "Parovoz", "Tral", "Labo", "Dagruz", "Sprinter"]

COUNTRIES = [
    ("O'zbekiston", 265), ("Belarus", 1), ("Germaniya", 1), ("Gruziya", 1),
    ("Qoraqalpoq", 3),   ("Qozog'iston", 2), ("Rossiya", 12), ("Turkiya", 1),
]

DIRECTIONS = [
    "Toshkent → Rossiya", "Toshkent → Moskva",
    "Samarqand → Moskva", "Buxoro → Qozog'iston",
    "Namangan → Toshkent", "Toshkent → Stambul",
    "Toshkent → Baku",    "Toshkent → Germaniya",
]

LANG = {
    "uz": {
        "quick":    "🔍 Tezkor Qidiruv",
        "truck":    "🚛 Moshina topish",
        "cargo":    "📦 Yuk topish",
        "post":     "📢 E'lon qo'shish",
        "my":       "📋 Mening e'lonlarim",
        "settings": "⚙️ Sozlamalar",
        "back":     "⬅️ Orqaga",
        "cancel":   "❌ Bekor qilish",
        "chg_trk":  "🚗 Avto turini o'zgartirish",
        "more":     "📋 Ko'proq ko'rsatish",
    },
    "ru": {
        "quick":    "🔍 Быстрый поиск",
        "truck":    "🚛 Найти машину",
        "cargo":    "📦 Найти груз",
        "post":     "📢 Добавить объявление",
        "my":       "📋 Мои объявления",
        "settings": "⚙️ Настройки",
        "back":     "⬅️ Назад",
        "cancel":   "❌ Отмена",
        "chg_trk":  "🚗 Изменить тип авто",
        "more":     "📋 Показать ещё",
    }
}

def t(key: str, lang: str = "uz") -> str:
    return LANG.get(lang, LANG["uz"]).get(key, key)


def main_kb(lang: str = "uz", user_id: int = 0, first_name: str = "", username: str = "", photo: str = "") -> ReplyKeyboardMarkup:
    L = t
    webapp_btn_txt = "🌐 Web App"
    rows = []

    # Web App button (only if URL is configured) — pass user data via URL params
    _url = _build_webapp_url(user_id, first_name, username, photo)
    if _url:
        rows.append([KeyboardButton(
            text=webapp_btn_txt,
            web_app=WebAppInfo(url=_url)
        )])

    rows += [
        [KeyboardButton(text=L("quick", lang))],
        [KeyboardButton(text=L("truck", lang)), KeyboardButton(text=L("cargo", lang))],
        [KeyboardButton(text=L("post", lang))],
        [KeyboardButton(text=L("my", lang)), KeyboardButton(text=L("settings", lang))],
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=rows)


def search_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=t("chg_trk", lang))],
        [KeyboardButton(text=t("back", lang))],
    ])


def back_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=t("back", lang))],
    ])


def cancel_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=t("cancel", lang))],
    ])


def result_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=t("chg_trk", lang))],
        [KeyboardButton(text=t("back", lang))],
    ])


def truck_type_kb(lang: str = "uz", current: str = "ALL") -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="Hammasi" if lang == "uz" else "Все")]]
    for i in range(1, len(TRUCKS), 2):
        row = [KeyboardButton(text=TRUCKS[i])]
        if i + 1 < len(TRUCKS):
            row.append(KeyboardButton(text=TRUCKS[i + 1]))
        rows.append(row)
    rows.append([KeyboardButton(text=t("back", lang))])
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=rows)


def countries_inline(lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for name, count in COUNTRIES:
        row.append(InlineKeyboardButton(
            text=f"{name} — {count}",
            callback_data=f"country:{name}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def directions_inline() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for d in DIRECTIONS:
        row.append(InlineKeyboardButton(text=d, callback_data=f"dir:{d}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ad_inline(ad_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    detail_txt = "Batafsil" if lang == "uz" else "Подробнее"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=detail_txt, callback_data=f"detail:{ad_id}")
    ]])


def detail_inline(ad_id: int, phone: str, link: str, lang: str = "uz") -> InlineKeyboardMarkup:
    ph_txt   = "📞 Telefon raqam" if lang == "uz" else "📞 Телефон"
    link_txt = "🔗 Xabarga o'tish" if lang == "uz" else "🔗 Перейти в чат"
    rows = []
    # "Xabarga o'tish" first when link is available
    if link:
        rows.append([InlineKeyboardButton(text=link_txt, url=link)])
    # Phone button always shown (shows phone via callback)
    rows.append([InlineKeyboardButton(text=ph_txt, callback_data=f"phone:{ad_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_ads_inline(ads: list, lang: str = "uz") -> InlineKeyboardMarkup:
    del_txt = "🗑 O'chirish" if lang == "uz" else "🗑 Удалить"
    buttons = []
    for ad in ads:
        buttons.append([InlineKeyboardButton(
            text=f"{ad['from_loc']} → {ad['to_loc']} — {del_txt}",
            callback_data=f"del:{ad['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def confirm_delete_inline(ad_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    yes = "✅ Ha, o'chirish" if lang == "uz" else "✅ Да, удалить"
    no  = "❌ Yo'q" if lang == "uz" else "❌ Нет"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=yes, callback_data=f"delconfirm:{ad_id}"),
        InlineKeyboardButton(text=no,  callback_data="delcancel"),
    ]])


def lang_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbek",   callback_data="setlang:uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
    ]])


def webapp_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    _url = _get_webapp_url()
    if not _url:
        return main_kb(lang)
    btn_txt = "🌐 Web App ochish" if lang == "uz" else "🌐 Открыть Web App"
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=btn_txt, web_app=WebAppInfo(url=_url))],
        *main_kb(lang).keyboard
    ])
