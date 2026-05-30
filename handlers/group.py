"""
Telethon userbot — faqat monitored guruhlardan xabarlarni o'qiydi,
bitta xabardagi 4-5 ta zayafkani ajratadi va SQLite bazaga saqlaydi.
"""
import re
import asyncio
import logging
from telethon import TelegramClient, events
from config import Config
from utils.db import add_ad, get_monitored_group_ids

logger = logging.getLogger(__name__)

# ── Truck keywords ──────────────────────────────────────────────────────────
TRUCK_KEYWORDS = {
    "ref rejimsiz": "Ref rejimsiz", "ref rejimsiZ": "Ref rejimsiz",
    "реф без режима": "Ref rejimsiz", "bez rejim": "Ref rejimsiz",
    "ref": "Ref", "реф": "Ref", "рефрижератор": "Ref",
    "tent": "Tent", "тент": "Tent",
    "izoterma": "Izoterma", "изотерм": "Izoterma",
    "katta isuzu": "Katta Isuzu", "большой исузу": "Katta Isuzu",
    "kichkina isuzu": "Kichkina Isuzu", "малый исузу": "Kichkina Isuzu",
    "isuzu": "Kichkina Isuzu",
    "bortovoy": "Bortovoy", "бортовой": "Bortovoy",
    "konteyner": "Konteyner", "контейнер": "Konteyner",
    "самосвал": "Bortovoy", "samosvol": "Bortovoy",
}

WEIGHT_RE = re.compile(r'(\d+[\.,]?\d*)\s*(т|t|тонн|ton)', re.IGNORECASE)
PHONE_RE  = re.compile(r'(\+?[0-9][\d\s\-\(\)]{8,14}[0-9])')
CITY_RE   = re.compile(
    r'\b(Toshkent|Samarqand|Buxoro|Namangan|Andijon|Farg[\'']?ona|Nukus|Termiz|Urganch|'
    r'Qarshi|Guliston|Navoiy|Chirchiq|Jizzax|Denov|Gazalkent|'
    r'Moskva|Peterburg|Rossiya|Russia|Qozog[\'']?iston|Kazakhstan|Bishkek|Qirg[\'']?iziston|'
    r'Stambul|Istanbul|Germaniya|Germany|Belarus|Gruziya|Georgia|Baku|Ozarbayjon|'
    r'Tojikiston|Tajikistan|Afg[\'']?oniston|Afghanistan|Eron|Iran|'
    r'Ташкент|Самарканд|Бухара|Наманган|Андижан|Фергана|Нукус|Термез|Ургенч|'
    r'Москва|Питер|Россия|Казахстан|Бишкек|Стамбул|Германия|Беларусь|Грузия|Баку|'
    r'Таджикистан|Афганистан|Иран)\b',
    re.IGNORECASE
)
PRICE_RE  = re.compile(r'(\d[\d\s\u202f]*(?:usd|uzs|\$|сум|sum|so[\'']?m|у\.с|у/с))', re.IGNORECASE)

# ── Multi-request splitter ──────────────────────────────────────────────────

def split_into_chunks(text: str) -> list[str]:
    """
    Bitta xabarda bir nechta zayafka bo'lsa ajratadi.
    Usullar (tartibda):
      1. Raqamli ro'yxat: "1.", "2.", "1)", "2)" va hokazo
      2. --- yoki *** separatorlar
      3. Ikki yoki undan ko'p bo'sh qator
    """
    # 1. Numbered list splitting
    numbered = re.split(r'\n\s*(?=\d{1,2}[.)]\s)', text)
    if len(numbered) > 1:
        return [c.strip() for c in numbered if c.strip()]

    # 2. Separator lines
    sep = re.split(r'\n\s*[-—=*]{3,}\s*\n', text)
    if len(sep) > 1:
        return [c.strip() for c in sep if c.strip()]

    # 3. Double blank lines
    parts = re.split(r'\n\s*\n\s*\n', text)
    if len(parts) > 1:
        return [c.strip() for c in parts if c.strip()]

    return [text.strip()]


def parse_single_ad(text: str) -> dict | None:
    """Parse one logistics ad chunk."""
    if not text or len(text) < 15:
        return None

    text_lower = text.lower()

    cities = CITY_RE.findall(text)
    if len(cities) < 2:
        return None

    from_loc = cities[0]
    to_loc   = cities[1]

    weight_m = WEIGHT_RE.search(text)
    weight   = f"{weight_m.group(1)}t" if weight_m else ""

    truck = ""
    for kw, val in TRUCK_KEYWORDS.items():
        if kw in text_lower:
            truck = val
            break

    phone_m = PHONE_RE.search(text)
    phone   = phone_m.group(1).strip() if phone_m else ""

    price_m = PRICE_RE.search(text)
    price   = price_m.group(0).strip() if price_m else ""

    # Cargo: try to find after keywords like "yuk:", "груз:", "cargo:"
    cargo = ""
    cargo_m = re.search(r'(?:yuk|груз|cargo|tovar|товар)\s*[:\-]?\s*([^\n,]{3,40})', text, re.IGNORECASE)
    if cargo_m:
        cargo = cargo_m.group(1).strip()

    return {
        "from_loc": from_loc,
        "to_loc":   to_loc,
        "weight":   weight,
        "truck":    truck,
        "cargo":    cargo,
        "price":    price,
        "km":       0,
        "hours":    0,
        "phone":    phone,
        "link":     "",
        "customs":  "",
        "source":   "Telegram",
        "group_id": 0,
        "message_id": 0,
    }


def parse_all_ads(text: str) -> list[dict]:
    """Split message and parse each chunk. Returns list of valid ads."""
    chunks = split_into_chunks(text)
    results = []
    for chunk in chunks:
        ad = parse_single_ad(chunk)
        if ad:
            results.append(ad)
    return results


def make_link(chat, msg_id: int) -> str:
    """Build a direct Telegram link to the message."""
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{msg_id}"

    # Private supergroup: id is like -1001234567890
    raw_id = getattr(chat, "id", 0)
    if raw_id < 0:
        # Remove -100 prefix
        s = str(abs(raw_id))
        if s.startswith("100"):
            s = s[3:]
        return f"https://t.me/c/{s}/{msg_id}"

    return ""


def normalize_group_id(raw_id: int) -> int:
    """Return the bare group ID (without -100 prefix) for DB storage."""
    s = str(abs(raw_id))
    if s.startswith("100") and len(s) > 10:
        return int(s[3:])
    return abs(raw_id)


# ── Userbot ────────────────────────────────────────────────────────────────

# In-memory cache of monitored group IDs (refreshed every 60s)
_monitored_cache: set[int] = set()
_cache_ts: float = 0.0
_CACHE_TTL = 60.0  # seconds


async def _refresh_cache():
    global _monitored_cache, _cache_ts
    import time
    if time.time() - _cache_ts > _CACHE_TTL:
        _monitored_cache = await get_monitored_group_ids()
        _cache_ts = time.time()
        logger.info(f"Monitored groups cache: {_monitored_cache}")


async def start_userbot():
    """Start the Telethon userbot if API credentials are configured."""
    if not Config.API_ID or not Config.API_HASH or not Config.PHONE:
        logger.info("Userbot disabled — API_ID/API_HASH/PHONE not set in .env")
        return

    client = TelegramClient(Config.SESSION, Config.API_ID, Config.API_HASH)
    await client.start(phone=Config.PHONE)
    logger.info("Userbot started ✅")

    # Initial cache load
    await _refresh_cache()

    @client.on(events.NewMessage())
    async def on_new_msg(event):
        try:
            await _refresh_cache()

            # Filter: only process messages from monitored groups
            chat_id = event.chat_id
            if not _monitored_cache:
                # No groups configured yet — skip all
                return

            # Normalize: try both raw ID and without -100 prefix
            bare_id = normalize_group_id(chat_id)
            if chat_id not in _monitored_cache and bare_id not in _monitored_cache:
                return

            text = event.raw_text
            if not text:
                return

            chat   = await event.get_chat()
            msg_id = event.id
            link   = make_link(chat, msg_id)
            source = getattr(chat, "title", "Telegram")[:50]

            ads = parse_all_ads(text)
            if not ads:
                return

            for ad in ads:
                ad["link"]       = link
                ad["source"]     = source
                ad["group_id"]   = bare_id
                ad["message_id"] = msg_id
                await add_ad(ad)
                logger.info(f"✅ Saved ad: {ad['from_loc']}→{ad['to_loc']} from group {bare_id} msg {msg_id}")

        except Exception as e:
            logger.debug(f"Parse error: {e}")

    await client.run_until_disconnected()
