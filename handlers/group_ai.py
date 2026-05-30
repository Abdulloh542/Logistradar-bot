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
import time
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
1. Imlo xatolarini tuzat: "teshent"→"Toshkent", "maskvaga"→"Moskva", "anjijin"→"Andijon" va h.k.
2. Bitta xabarda bir nechta zayafka bo'lsa — BARCHASINI ajrat
3. Yo'nalishni aniqlash: "КАШКАДАРЁ\nОмск" = Qashqadaryo → Omsk (birinchi shahar from_loc, ikkinchi to_loc). "-" yoki "→" belgisi bo'lsa: "Toshkent-Moskva" = Toshkent → Moskva
4. Logistika zayafkasi emas deb hisoblasang — bo'sh massiv [] qaytar
5. FAQAT JSON massiv qaytar, boshqa matn yozma

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
- phone: telefon raqam. +998 prefiksi bo'lmasa ham yoz (masalan "905976525" yoki "90 597 65 25" → "+998905976525"). Bo'sh bo'lsa ""
- Bitta xabarda BARCHA zayafkalar uchun bittadan phone bo'ladi (oxirida yozilgan raqam hammaga tegishli)

Misol natija: [{"from_loc":"Toshkent","to_loc":"Moskva","weight":"20t","truck":"Tent","cargo":"paxta","price":"800$","phone":"+998901234567"}]"""


def _fix_phones(ads: list) -> list:
    """Ensure all phones start with +998 (Uzbek prefix)."""
    for ad in ads:
        p = re.sub(r'[\s\-\(\)]', '', ad.get("phone") or "")
        if not p:
            continue
        # Already correct
        if p.startswith("+998") and len(p) == 13:
            ad["phone"] = p
            continue
        # Strip any wrong prefix (+7, +995, etc.)
        digits = re.sub(r'^\+?\d{1,3}', '', p) if p.startswith('+') else p
        # 9-digit Uzbek number
        m = re.search(r'(9[0-9]{8})', digits)
        if m:
            ad["phone"] = f"+998{m.group(1)}"
        elif re.match(r'^998[0-9]{9}$', p):
            ad["phone"] = f"+{p}"
        # else leave as-is
    return ads


# Rate limiter: max 1 request per 2 seconds to avoid Groq 429
_ai_lock = asyncio.Semaphore(1)
_last_ai_call: float = 0.0


async def parse_with_ai(text: str) -> list[dict]:
    """Use Groq LLaMA to extract zayafkas from message text."""
    if not Config.GROQ_API_KEY:
        return []
    global _last_ai_call
    async with _ai_lock:
        # Ensure at least 2s between calls
        wait = 2.0 - (time.time() - _last_ai_call)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            from groq import Groq
            client = Groq(api_key=Config.GROQ_API_KEY)

            def _call():
                return client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text[:3000]},
                    ],
                    max_tokens=4000,
                    temperature=0.1,
                )

            resp = await asyncio.to_thread(_call)
            _last_ai_call = time.time()
            raw = resp.choices[0].message.content.strip()

            m = re.search(r'\[.*\]', raw, re.DOTALL)
            if not m:
                return []
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return _fix_phones(data)
        except Exception as e:
            logger.warning(f"AI parse error: {e}")
            _last_ai_call = time.time()
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
