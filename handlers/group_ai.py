"""
AI-powered group message handler.
Bot guruhga a'zo bo'lganda barcha xabarlarni o'qiydi,
Groq AI (LLaMA) yordamida zayafkalarni ajratib saqlaydi.
Telethon/userbot kerak emas — faqat bot o'sha guruhga qo'shilgan bo'lsin.
"""
import json
import logging
import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message

from config import Config
from utils.db import add_ad, get_monitored_group_ids

logger = logging.getLogger(__name__)
router = Router()

# In-memory cache of monitored group IDs
_group_cache: set[int] = set()
_cache_ts: float = 0.0
_CACHE_TTL = 60.0


async def _get_groups() -> set[int]:
    global _group_cache, _cache_ts
    import time
    if time.time() - _cache_ts > _CACHE_TTL:
        _group_cache = await get_monitored_group_ids()
        _cache_ts = time.time()
    return _group_cache


def _normalize_chat_id(chat_id: int) -> int:
    s = str(abs(chat_id))
    if s.startswith("100") and len(s) > 10:
        return int(s[3:])
    return abs(chat_id)


def _make_link(chat_id: int, msg_id: int, username: str = "") -> str:
    if username:
        return f"https://t.me/{username}/{msg_id}"
    bare = _normalize_chat_id(chat_id)
    return f"https://t.me/c/{bare}/{msg_id}"


SYSTEM_PROMPT = """Sen logistika zayafkalarini (jo'natish/yetkazib berish buyurtmalari) ajratuvchi AI yordamchisisan.
Foydalanuvchi Telegram guruh xabarini beradi. Sen barcha logistika zayafkalarini JSON massiv sifatida qaytarasan.

Qoidalar:
1. Imlo xatolarini tuzat: "teshent"→"Toshkent", "maskvaga"→"Moskva", "angren"→"Angren" va h.k.
2. Bitta xabarda bir nechta zayafka bo'lsa — BARCHASINI ajrat
3. Logistika zayafkasi emas deb hisoblasang — bo'sh massiv [] qaytar
4. FAQAT JSON massiv qaytar, boshqa matn yozma

Har zayafka uchun maydonlar:
- from_loc: jo'nab ketish joyi
- to_loc: borish joyi
- weight: og'irlik ("20t", "22-23 тонна", bo'sh bo'lsa "")
- truck: transport turi. Quyidagilardan birini tanlang:
  Tent, Ref, Ref rejimsiz, Izoterma, Kichkina Isuzu, Katta Isuzu, Bortovoy, Konteyner,
  Chakman, Kamaz, Mega, Ploshadka, Parovoz, Tral, Labo, Dagruz, Sprinter
  (mos kelmasa bo'sh "")
- cargo: yuk nomi ("kaolin", "meva" yoki "")
- price: narx ("1200$", "kelishiladi" yoki "")
- phone: telefon raqam yoki ""

Misol natija: [{"from_loc":"Toshkent","to_loc":"Moskva","weight":"20t","truck":"Tent","cargo":"paxta","price":"800$","phone":"+998901234567"}]"""


async def parse_with_ai(text: str) -> list[dict]:
    """Use Groq LLaMA to extract zayafkas from message text."""
    if not Config.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set")
        return []
    try:
        from groq import Groq
        client = Groq(api_key=Config.GROQ_API_KEY)

        def _call():
            return client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:2000]},
                ],
                max_tokens=1000,
                temperature=0.1,
            )

        resp = await asyncio.to_thread(_call)
        raw = resp.choices[0].message.content.strip()

        # Extract JSON array
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(0))
        if isinstance(data, list):
            return data
    except Exception as e:
        logger.warning(f"AI parse error: {e}")
    return []


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def on_group_message(msg: Message):
    """Handle all group messages from monitored groups."""
    try:
        groups = await _get_groups()
        if not groups:
            return

        chat_id = msg.chat.id
        bare_id = _normalize_chat_id(chat_id)

        # Check if this group is monitored
        if chat_id not in groups and bare_id not in groups:
            return

        text = msg.text or msg.caption
        if not text or len(text.strip()) < 15:
            return

        logger.info(f"📨 Group {bare_id} msg#{msg.message_id}: {text[:60]}...")

        ads = await parse_with_ai(text)
        if not ads:
            return

        username = msg.chat.username or ""
        link     = _make_link(chat_id, msg.message_id, username)
        source   = msg.chat.title or f"Guruh {bare_id}"

        saved = 0
        for ad in ads:
            from_loc = (ad.get("from_loc") or "").strip()
            to_loc   = (ad.get("to_loc") or "").strip()
            if not from_loc or not to_loc:
                continue

            await add_ad({
                "from_loc":   from_loc,
                "to_loc":     to_loc,
                "weight":     (ad.get("weight") or "").strip(),
                "truck":      (ad.get("truck") or "").strip(),
                "cargo":      (ad.get("cargo") or "").strip(),
                "price":      (ad.get("price") or "").strip(),
                "km":         0,
                "hours":      0,
                "phone":      (ad.get("phone") or "").strip(),
                "link":       link,
                "customs":    "",
                "source":     source,
                "group_id":   bare_id,
                "message_id": msg.message_id,
                "raw_text":   text,
            })
            saved += 1
            logger.info(f"  ✅ {from_loc}→{to_loc} | {ad.get('truck','')} | {ad.get('phone','—')}")

        if saved:
            logger.info(f"  💾 {saved} ta zayafka saqlandi (guruh {bare_id})")

    except Exception as e:
        logger.error(f"Group handler error: {e}")
