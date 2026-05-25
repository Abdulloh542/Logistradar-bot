from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage

from utils import db
from utils import keyboards as kb
from utils import texts as tx
from config import Config

router = Router()

PAGE = 10

# ─── FSM ───────────────────────────────────────────────
class PostAd(StatesGroup):
    from_loc = State()
    to_loc   = State()
    weight   = State()
    truck    = State()
    cargo    = State()
    price    = State()
    phone    = State()

class Searching(StatesGroup):
    waiting = State()

# ─── helpers ───────────────────────────────────────────
async def u(uid: int) -> dict:
    return await db.get_user(uid)

async def lang(uid: int) -> str:
    return (await u(uid)).get("lang", "uz")

async def truck_pref(uid: int) -> str:
    return (await u(uid)).get("truck", "ALL")

BACK_TEXTS   = {"⬅️ Orqaga", "⬅️ Назад"}
CANCEL_TEXTS = {"❌ Bekor qilish", "❌ Отмена"}
MENU_TEXTS   = {
    "🔍 Tezkor Qidiruv", "🔍 Быстрый поиск",
    "🚛 Moshina topish", "🚛 Найти машину",
    "📦 Yuk topish",     "📦 Найти груз",
    "📢 E'lon qo'shish", "📢 Добавить объявление",
    "📋 Mening e'lonlarim", "📋 Мои объявления",
    "⚙️ Sozlamalar",     "⚙️ Настройки",
    "🚗 Avto turini o'zgartirish", "🚗 Изменить тип авто",
}
TRUCK_TEXTS = {"Hammasi", "Все", "Tent", "Ref", "Ref rejimsiz", "Izoterma",
               "Kichkina Isuzu", "Katta Isuzu", "Bortovoy", "Konteyner"}

async def _get_photo_url(bot: Bot, uid: int) -> str:
    """Get user's Telegram profile photo URL via Bot API."""
    try:
        photos = await bot.get_user_profile_photos(uid, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id  # largest size
            file = await bot.get_file(file_id)
            return f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file.file_path}"
    except Exception:
        pass
    return ""

# ─── /start ────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext, bot: Bot):
    await state.clear()
    uid = msg.from_user.id
    row = await u(uid)
    lg  = row.get("lang", "uz")
    await db.save_user(uid, lg, row.get("truck","ALL"), msg.from_user.username or "")
    first = msg.from_user.first_name or ""
    uname = msg.from_user.username or ""
    photo = await _get_photo_url(bot, uid)
    await msg.answer(tx.txt("welcome", lg), reply_markup=kb.main_kb(lg, uid, first, uname, photo))

# ─── BACK / CANCEL (work from any state) ───────────────
@router.message(F.text.in_(BACK_TEXTS))
async def on_back(msg: Message, state: FSMContext):
    await state.clear()
    lg = await lang(msg.from_user.id)
    first = msg.from_user.first_name or ""
    uname = msg.from_user.username or ""
    await msg.answer("🏠", reply_markup=kb.main_kb(lg, msg.from_user.id, first, uname))

@router.message(F.text.in_(CANCEL_TEXTS))
async def on_cancel(msg: Message, state: FSMContext):
    await state.clear()
    lg = await lang(msg.from_user.id)
    first = msg.from_user.first_name or ""
    uname = msg.from_user.username or ""
    await msg.answer(tx.txt("cancelled", lg), reply_markup=kb.main_kb(lg, msg.from_user.id, first, uname))

# ─── MAIN MENU ─────────────────────────────────────────
@router.message(F.text.in_({"🔍 Tezkor Qidiruv", "🔍 Быстрый поиск"}))
async def on_quick(msg: Message, state: FSMContext):
    await state.clear()
    lg = await lang(msg.from_user.id)
    await state.set_state(Searching.waiting)
    await msg.answer(tx.txt("search_hint", lg), reply_markup=kb.search_kb(lg))

@router.message(F.text.in_({"🚛 Moshina topish", "🚛 Найти машину"}))
async def on_find_truck(msg: Message, state: FSMContext):
    await state.clear()
    lg = await lang(msg.from_user.id)
    await msg.answer(tx.txt("find_truck_msg", lg), reply_markup=kb.back_kb(lg))
    await msg.answer("👇", reply_markup=kb.countries_inline(lg))

@router.message(F.text.in_({"📦 Yuk topish", "📦 Найти груз"}))
async def on_find_cargo(msg: Message, state: FSMContext):
    await state.clear()
    lg = await lang(msg.from_user.id)
    await msg.answer(tx.txt("find_cargo_msg", lg), reply_markup=kb.back_kb(lg))
    await msg.answer("👇", reply_markup=kb.directions_inline())

@router.message(F.text.in_({"📢 E'lon qo'shish", "📢 Добавить объявление"}))
async def on_post(msg: Message, state: FSMContext):
    await state.clear()
    lg = await lang(msg.from_user.id)
    await state.set_state(PostAd.from_loc)
    await msg.answer(tx.txt("post_steps", lg)[0], reply_markup=kb.cancel_kb(lg))

@router.message(F.text.in_({"📋 Mening e'lonlarim", "📋 Мои объявления"}))
async def on_my_ads(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    lg  = await lang(uid)
    ads = await db.get_user_ads(uid)
    if not ads:
        await msg.answer(tx.txt("my_ads_empty", lg), reply_markup=kb.back_kb(lg))
        return
    await msg.answer(tx.txt("my_ads_header", lg, count=len(ads)), reply_markup=kb.back_kb(lg))
    for ad in ads:
        text = tx.txt("my_ad_item", lg,
            from_loc=ad["from_loc"], to_loc=ad["to_loc"],
            weight=ad.get("weight","—"), truck=ad.get("truck","—"),
            cargo=ad.get("cargo","—"), price=ad.get("price","—"),
            phone=ad.get("phone","—"), created=str(ad.get("created",""))[:10])
        inline = kb.my_ads_inline([ad], lg)
        await msg.answer(text, reply_markup=inline)

@router.message(F.text.in_({"⚙️ Sozlamalar", "⚙️ Настройки"}))
async def on_settings(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    row = await u(uid)
    lg  = row.get("lang","uz")
    tk  = row.get("truck","ALL")
    lang_label = "🇺🇿 O'zbek" if lg == "uz" else "🇷🇺 Русский"
    await msg.answer(tx.txt("settings", lg, lang=lang_label, truck=tk), reply_markup=kb.back_kb(lg))
    await msg.answer("👇", reply_markup=kb.lang_inline())

@router.message(F.text.in_({"🚗 Avto turini o'zgartirish", "🚗 Изменить тип авто"}))
async def on_chg_truck(msg: Message, state: FSMContext):
    # Only outside PostAd
    cur = await state.get_state()
    if cur and cur.startswith("PostAd"):
        return
    await state.clear()
    uid = msg.from_user.id
    lg  = await lang(uid)
    tk  = await truck_pref(uid)
    await msg.answer(tx.txt("truck_select", lg), reply_markup=kb.truck_type_kb(lg, tk))

# ─── TRUCK TYPE (global, outside PostAd) ───────────────
@router.message(F.text.in_(TRUCK_TEXTS), ~StateFilter(PostAd))
async def on_truck_global(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    lg  = await lang(uid)
    row = await u(uid)
    val = "ALL" if msg.text in ("Hammasi", "Все") else msg.text
    await db.save_user(uid, lg, val, row.get("username",""))
    await msg.answer(tx.txt("truck_selected", lg, truck=msg.text), reply_markup=kb.search_kb(lg))
    await state.set_state(Searching.waiting)

# ─── SEARCH ────────────────────────────────────────────
@router.message(Searching.waiting, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS | MENU_TEXTS | TRUCK_TEXTS))
async def on_search(msg: Message, state: FSMContext):
    uid   = msg.from_user.id
    lg    = await lang(uid)
    query = msg.text.strip()
    tk    = await truck_pref(uid)

    ads, total = await db.search_ads(query, tk, limit=PAGE)
    fallback = False
    if not ads:
        ads, total = await db.search_ads("", "ALL", limit=PAGE)
        fallback = True

    if fallback:
        await msg.answer(tx.txt("no_results", lg))
    else:
        today = max(1, total // 3)
        await msg.answer(tx.txt("results_header", lg, count=total, today=today))

    await state.update_data(query=query, offset=PAGE, total=total)
    await _send_cards(msg, ads, 1, lg)

async def _send_cards(msg: Message, ads: list, start_n: int, lg: str):
    for i, ad in enumerate(ads):
        text = tx.format_ad_card(ad, start_n + i, lg)
        await msg.answer(text, reply_markup=kb.ad_inline(ad["id"], lg))

# ─── POST AD FSM ────────────────────────────────────────
@router.message(PostAd.from_loc, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS))
async def post_from(msg: Message, state: FSMContext):
    lg = await lang(msg.from_user.id)
    await state.update_data(from_loc=msg.text)
    await state.set_state(PostAd.to_loc)
    await msg.answer(tx.txt("post_steps", lg)[1])

@router.message(PostAd.to_loc, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS))
async def post_to(msg: Message, state: FSMContext):
    lg = await lang(msg.from_user.id)
    await state.update_data(to_loc=msg.text)
    await state.set_state(PostAd.weight)
    await msg.answer(tx.txt("post_steps", lg)[2])

@router.message(PostAd.weight, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS))
async def post_weight(msg: Message, state: FSMContext):
    lg = await lang(msg.from_user.id)
    uid = msg.from_user.id
    row = await u(uid)
    await state.update_data(weight=msg.text)
    await state.set_state(PostAd.truck)
    await msg.answer(tx.txt("post_steps", lg)[3],
                     reply_markup=kb.truck_type_kb(lg, row.get("truck","ALL")))

@router.message(PostAd.truck, F.text.in_(TRUCK_TEXTS))
async def post_truck(msg: Message, state: FSMContext):
    lg = await lang(msg.from_user.id)
    await state.update_data(truck=msg.text)
    await state.set_state(PostAd.cargo)
    await msg.answer(tx.txt("post_steps", lg)[4], reply_markup=kb.cancel_kb(lg))

@router.message(PostAd.cargo, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS))
async def post_cargo(msg: Message, state: FSMContext):
    lg = await lang(msg.from_user.id)
    await state.update_data(cargo=msg.text)
    await state.set_state(PostAd.price)
    await msg.answer(tx.txt("post_steps", lg)[5])

@router.message(PostAd.price, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS))
async def post_price(msg: Message, state: FSMContext):
    lg = await lang(msg.from_user.id)
    await state.update_data(price=msg.text)
    await state.set_state(PostAd.phone)
    await msg.answer(tx.txt("post_steps", lg)[6])

@router.message(PostAd.phone, ~F.text.in_(BACK_TEXTS | CANCEL_TEXTS))
async def post_phone(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    lg  = await lang(uid)
    await state.update_data(phone=msg.text)
    data = await state.get_data()
    await state.clear()

    await db.add_user_ad(uid, {
        "from_loc": data.get("from_loc",""),
        "to_loc":   data.get("to_loc",""),
        "weight":   data.get("weight","—"),
        "truck":    data.get("truck","—"),
        "cargo":    data.get("cargo","—"),
        "price":    data.get("price","—"),
        "phone":    msg.text,
    })

    await msg.answer(tx.txt("post_confirm", lg,
        from_loc=data.get("from_loc",""), to_loc=data.get("to_loc",""),
        weight=data.get("weight","—"), truck=data.get("truck","—"),
        cargo=data.get("cargo","—"), price=data.get("price","—"),
        phone=msg.text
    ), reply_markup=kb.main_kb(lg))

# ─── CALLBACKS ─────────────────────────────────────────
@router.callback_query(F.data.startswith("country:"))
async def cb_country(cb: CallbackQuery):
    await cb.answer()
    uid     = cb.from_user.id
    lg      = await lang(uid)
    country = cb.data.split(":",1)[1]
    tk      = await truck_pref(uid)
    ads, total = await db.search_ads(country, tk, limit=PAGE)
    if not ads:
        ads, total = await db.search_ads("", "ALL", limit=PAGE)
    today = max(1, total // 3)
    await cb.message.answer(tx.txt("results_header", lg, count=total, today=today))
    await _send_cards(cb.message, ads, 1, lg)
    await cb.message.answer("🔍", reply_markup=kb.result_kb(lg))

@router.callback_query(F.data.startswith("dir:"))
async def cb_dir(cb: CallbackQuery):
    await cb.answer()
    uid = cb.from_user.id
    lg  = await lang(uid)
    tk  = await truck_pref(uid)
    direction = cb.data.split(":",1)[1]
    query = direction.replace("→"," ")
    ads, total = await db.search_ads(query, tk, limit=PAGE)
    if not ads:
        ads, total = await db.search_ads("", "ALL", limit=PAGE)
    today = max(1, total // 3)
    await cb.message.answer(tx.txt("results_header", lg, count=total, today=today))
    await _send_cards(cb.message, ads, 1, lg)
    await cb.message.answer("🔍", reply_markup=kb.result_kb(lg))

@router.callback_query(F.data.startswith("detail:"))
async def cb_detail(cb: CallbackQuery):
    await cb.answer()
    uid   = cb.from_user.id
    lg    = await lang(uid)
    ad_id = int(cb.data.split(":",1)[1])
    ads, _ = await db.search_ads("", "ALL", limit=9999)
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        await cb.answer("Topilmadi", show_alert=True)
        return
    text = tx.format_ad_detail(ad, lg)
    await cb.message.answer(text,
        reply_markup=kb.detail_inline(ad_id, ad.get("phone",""), ad.get("link",""), lg))

@router.callback_query(F.data.startswith("phone:"))
async def cb_phone(cb: CallbackQuery):
    uid   = cb.from_user.id
    lg    = await lang(uid)
    ad_id = int(cb.data.split(":",1)[1])
    ads, _ = await db.search_ads("", "ALL", limit=9999)
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad or not ad.get("phone"):
        await cb.answer(tx.txt("no_phone", lg), show_alert=True)
        return
    await cb.answer()
    await cb.message.answer(tx.txt("phone_reveal", lg, phone=ad["phone"]))

@router.callback_query(F.data.startswith("del:"))
async def cb_del_ask(cb: CallbackQuery):
    await cb.answer()
    lg    = await lang(cb.from_user.id)
    ad_id = int(cb.data.split(":",1)[1])
    await cb.message.edit_reply_markup(reply_markup=kb.confirm_delete_inline(ad_id, lg))

@router.callback_query(F.data.startswith("delconfirm:"))
async def cb_del_yes(cb: CallbackQuery):
    await cb.answer()
    uid   = cb.from_user.id
    lg    = await lang(uid)
    ad_id = int(cb.data.split(":",1)[1])
    await db.delete_user_ad(ad_id, uid)
    await cb.message.edit_text(tx.txt("deleted", lg))

@router.callback_query(F.data == "delcancel")
async def cb_del_no(cb: CallbackQuery):
    await cb.answer(tx.txt("delete_cancel", await lang(cb.from_user.id)))

@router.callback_query(F.data.startswith("setlang:"))
async def cb_lang(cb: CallbackQuery):
    await cb.answer()
    uid  = cb.from_user.id
    lg   = cb.data.split(":",1)[1]
    row  = await u(uid)
    await db.save_user(uid, lg, row.get("truck","ALL"), row.get("username",""))
    await cb.message.answer(tx.txt("lang_set", lg), reply_markup=kb.main_kb(lg))
