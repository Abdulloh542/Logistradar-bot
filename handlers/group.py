"""
Telethon userbot — 300+ logistika guruhlaridan xabarlarni o'qiydi
va SQLite bazaga saqlaydi.
"""
import re
import logging
from telethon import TelegramClient, events
from config import Config
from utils.db import add_ad

logger = logging.getLogger(__name__)

TRUCK_KEYWORDS = {
    "tent": "Tent", "тент": "Tent",
    "ref rejimsiz": "Ref rejimsiz", "реф без режима": "Ref rejimsiz",
    "ref": "Ref", "реф": "Ref",
    "izoterma": "Izoterma", "изотерм": "Izoterma",
    "kichkina isuzu": "Kichkina Isuzu", "малый исузу": "Kichkina Isuzu",
    "isuzu": "Kichkina Isuzu",
    "katta isuzu": "Katta Isuzu", "большой исузу": "Katta Isuzu",
    "bortovoy": "Bortovoy", "бортовой": "Bortovoy",
    "konteyner": "Konteyner", "контейнер": "Konteyner",
}

WEIGHT_RE = re.compile(r'(\d+[\.,]?\d*)\s*(т|t|тонн|ton)', re.IGNORECASE)
PHONE_RE  = re.compile(r'(\+?[\d\s\-\(\)]{9,15})')
CITY_RE   = re.compile(r'(Toshkent|Samarqand|Buxoro|Namangan|Andijon|Farg.ona|Nukus|Termiz|Urganch|'
                        r'Moskva|Rossiya|Qozog.iston|Bishkek|Stambul|Germaniya|Belarus|Gruziya|Baku|'
                        r'Ташкент|Самарканд|Бухара|Наманган|Андижан|Москва|Россия|Казахстан|Бишкек)',
                        re.IGNORECASE)

def parse_ad(text: str) -> dict | None:
    """Parse logistics ad from group message text."""
    if not text or len(text) < 20:
        return None
    text_lower = text.lower()

    # Find cities
    cities = CITY_RE.findall(text)
    if len(cities) < 2:
        return None

    from_loc = cities[0]
    to_loc   = cities[1]

    # Weight
    weight_m = WEIGHT_RE.search(text)
    weight = f"{weight_m.group(1)}t" if weight_m else ""

    # Truck type
    truck = ""
    for kw, val in TRUCK_KEYWORDS.items():
        if kw in text_lower:
            truck = val
            break

    # Phone
    phone_m = PHONE_RE.search(text)
    phone = phone_m.group(1).strip() if phone_m else ""

    # Price (look for USD, $, сум, so'm)
    price_m = re.search(r'(\d[\d\s]*(?:usd|uzs|\$|сум|sum|so.m))', text, re.IGNORECASE)
    price = price_m.group(0).strip() if price_m else ""

    return {
        "from_loc": from_loc,
        "to_loc":   to_loc,
        "weight":   weight,
        "truck":    truck,
        "cargo":    "",
        "price":    price,
        "km":       0,
        "hours":    0,
        "phone":    phone,
        "link":     "",
        "customs":  "",
        "source":   "Telegram",
    }


async def start_userbot():
    """Start the Telethon userbot if API credentials are configured."""
    if not Config.API_ID or not Config.API_HASH or not Config.PHONE:
        logger.info("Userbot disabled — API_ID/API_HASH/PHONE not set in .env")
        return

    client = TelegramClient(Config.SESSION, Config.API_ID, Config.API_HASH)
    await client.start(phone=Config.PHONE)
    logger.info("Userbot started successfully")

    @client.on(events.NewMessage())
    async def on_new_msg(event):
        try:
            text = event.raw_text
            if not text:
                return
            ad = parse_ad(text)
            if ad:
                link = ""
                try:
                    chat = await event.get_chat()
                    msg_id = event.id
                    if hasattr(chat, "username") and chat.username:
                        link = f"https://t.me/{chat.username}/{msg_id}"
                    ad["source"] = getattr(chat, "title", "Telegram")[:50]
                    ad["link"] = link
                except Exception:
                    pass
                await add_ad(ad)
        except Exception as e:
            logger.debug(f"Parse error: {e}")

    await client.run_until_disconnected()
