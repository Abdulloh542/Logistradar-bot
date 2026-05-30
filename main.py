import asyncio
import json
import logging
import mimetypes
import os
import sqlite3
import urllib.parse
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from handlers import user
from handlers import admin
from handlers import group_ai
from utils.db import init_db, add_monitored_group

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"
DB_PATH    = Path(__file__).parent / "yukonuz.db"


# ── Webapp HTTP handlers ──────────────────────────────────────────────────────

def _get_ads(page=1, limit=20, q="", truck="ALL"):
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        conditions, params = [], []
        if q:
            for word in q.lower().split():
                conditions.append(
                    "(LOWER(from_loc)||' '||LOWER(to_loc)||' '||LOWER(cargo)||' '||LOWER(source)) LIKE ?"
                )
                params.append(f"%{word}%")
        if truck and truck != "ALL":
            conditions.append("LOWER(truck) LIKE ?")
            params.append(f"%{truck.lower()}%")
        where  = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * limit
        cur.execute(f"SELECT COUNT(*) FROM ads {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT * FROM ads {where} ORDER BY created DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return {"total": total, "page": page, "limit": limit, "ads": rows}
    except Exception as e:
        return {"total": 0, "page": 1, "limit": limit, "ads": [], "error": str(e)}


async def api_ads(request: web.Request) -> web.Response:
    qs    = request.rel_url.query
    page  = int(qs.get("page",  "1"))
    limit = int(qs.get("limit", "20"))
    q     = qs.get("q",     "")
    truck = qs.get("truck", "ALL")
    data  = await asyncio.to_thread(_get_ads, page, limit, q, truck)
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def static_file(request: web.Request) -> web.Response:
    path = request.match_info.get("path", "index.html") or "index.html"
    fp   = WEBAPP_DIR / path
    if not fp.exists() or not fp.is_file():
        fp = WEBAPP_DIR / "index.html"
    mime, _ = mimetypes.guess_type(str(fp))
    return web.Response(
        body=fp.read_bytes(),
        content_type=mime or "application/octet-stream",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def start_web_server():
    port = int(os.environ.get("PORT", 7777))
    app  = web.Application()
    app.router.add_get("/api/ads", api_ads)
    app.router.add_get("/",            static_file)
    app.router.add_get("/{path:.+}",   static_file)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Webapp server started on port {port} ✅")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    if not Config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN .env faylda ko'rsatilmagan!")

    await init_db()

    # Seed default monitored groups
    await add_monitored_group(1411032261, "Logistika guruhi 1", 0)
    await add_monitored_group(1159400110, "Logistika guruhi 2", 0)
    await add_monitored_group(1489222508, "YUK TASHISH XIZMATLARI", 0)

    # Webapp server (same process)
    await start_web_server()

    # Bot
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)
    dp.include_router(group_ai.router)
    dp.include_router(user.router)

    # Userbot
    if Config.API_ID and Config.API_HASH:
        try:
            from handlers.group import start_userbot
            asyncio.create_task(start_userbot())
            logger.info("Userbot ishga tushdi")
        except ImportError:
            logger.warning("Telethon o'rnatilmagan, userbot ishlamaydi")
    else:
        logger.info("Userbot o'chirilgan — API_ID/API_HASH .env da yo'q")

    # Oldingi sessiyalarni tozalash (Conflict oldini olish)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot ishga tushdi ✅")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
