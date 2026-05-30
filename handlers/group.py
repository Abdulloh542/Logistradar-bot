"""
Telethon userbot — monitored guruhlardan xabarlarni o'qiydi,
Groq AI bilan zayafkalarni ajratib SQLite bazaga saqlaydi.
"""
import asyncio
import logging
from telethon import TelegramClient, events
from config import Config
from utils.db import add_ad, get_monitored_group_ids
from handlers.group_ai import parse_with_ai

logger = logging.getLogger(__name__)

_monitored_cache: set[int] = set()
_cache_ts: float = 0.0
_CACHE_TTL = 60.0


async def _refresh_cache():
    global _monitored_cache, _cache_ts
    import time
    if time.time() - _cache_ts > _CACHE_TTL:
        _monitored_cache = await get_monitored_group_ids()
        _cache_ts = time.time()
        logger.info(f"Monitored groups: {_monitored_cache}")


def _bare_id(raw_id: int) -> int:
    s = str(abs(raw_id))
    if s.startswith("100") and len(s) > 10:
        return int(s[3:])
    return abs(raw_id)


def _make_link(chat, msg_id: int) -> str:
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{msg_id}"
    raw_id = getattr(chat, "id", 0)
    bare = _bare_id(raw_id)
    return f"https://t.me/c/{bare}/{msg_id}"


async def start_userbot():
    if not Config.API_ID or not Config.API_HASH:
        logger.info("Userbot disabled — API_ID/API_HASH not set")
        return

    from telethon.sessions import StringSession
    session = StringSession(Config.SESSION_STRING) if Config.SESSION_STRING else Config.SESSION
    client = TelegramClient(session, Config.API_ID, Config.API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.warning("Userbot session not authorized — skipping")
        await client.disconnect()
        return

    me = await client.get_me()
    logger.info(f"Userbot started as: {me.first_name} (@{me.username}) ✅")

    await _refresh_cache()

    @client.on(events.NewMessage())
    async def on_new_msg(event):
        try:
            await _refresh_cache()
            if not _monitored_cache:
                return

            chat_id = event.chat_id
            bare    = _bare_id(chat_id)

            if chat_id not in _monitored_cache and bare not in _monitored_cache:
                return

            text = event.raw_text
            if not text or len(text.strip()) < 15:
                return

            chat   = await event.get_chat()
            msg_id = event.id
            link   = _make_link(chat, msg_id)
            source = getattr(chat, "title", f"Guruh {bare}")[:50]

            logger.info(f"📨 {source} ({bare}) msg#{msg_id}: {text[:60]}...")

            ads = await parse_with_ai(text)
            if not ads:
                return

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
                    "km": 0, "hours": 0,
                    "phone":      (ad.get("phone") or "").strip(),
                    "link":       link,
                    "customs":    "",
                    "source":     source,
                    "group_id":   bare,
                    "message_id": msg_id,
                    "raw_text":   text,
                })
                saved += 1
                logger.info(f"  ✅ {from_loc}→{to_loc} | {ad.get('truck','')} | {ad.get('phone','—')}")

            if saved:
                logger.info(f"  💾 {saved} zayafka saqlandi")

        except Exception as e:
            logger.debug(f"Msg error: {e}")

    await client.run_until_disconnected()
