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
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import Config
from handlers import user
from handlers import admin
from handlers import group_ai
from handlers import subscriptions
from utils.db import (
    init_db, add_monitored_group, get_stats, get_all_users,
    cleanup_old_ads, add_subscription, remove_subscription, get_user_subscriptions,
)
from utils import notify as _notify

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
            f"SELECT *, CAST(ROUND((JULIANDAY('now') - JULIANDAY(created)) * 1440) AS INTEGER) as ago "
            f"FROM ads {where} ORDER BY created DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return {"total": total, "page": page, "limit": limit, "ads": rows}
    except Exception as e:
        return {"total": 0, "page": 1, "limit": limit, "ads": [], "error": str(e)}


def _is_admin(uid: int) -> bool:
    return uid in Config.ADMIN_IDS


async def api_stats(request: web.Request) -> web.Response:
    uid = int(request.rel_url.query.get("uid", "0") or "0")
    if not _is_admin(uid):
        return web.Response(status=403, text="Forbidden")
    data = await get_stats()
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def api_users(request: web.Request) -> web.Response:
    uid = int(request.rel_url.query.get("uid", "0") or "0")
    if not _is_admin(uid):
        return web.Response(status=403, text="Forbidden")
    users = await get_all_users(limit=100)
    return web.Response(
        text=json.dumps({"users": users}, ensure_ascii=False),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def api_cleanup(request: web.Request) -> web.Response:
    uid = int(request.rel_url.query.get("uid", "0") or "0")
    if not _is_admin(uid):
        return web.Response(status=403, text="Forbidden")
    days = int(request.rel_url.query.get("days", "7") or "7")
    count = await cleanup_old_ads(days)
    return web.Response(
        text=json.dumps({"deleted": count}, ensure_ascii=False),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def api_is_admin(request: web.Request) -> web.Response:
    uid = int(request.rel_url.query.get("uid", "0") or "0")
    return web.Response(
        text=json.dumps({"is_admin": _is_admin(uid)}),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def api_subscriptions(request: web.Request) -> web.Response:
    uid = int(request.rel_url.query.get("uid", "0") or "0")
    if not uid:
        return web.Response(status=400, text="uid required")
    if request.method == "POST":
        body = await request.json()
        route = (body.get("route") or "").strip()
        if not route:
            return web.Response(status=400, text="route required")
        ok = await add_subscription(uid, route)
        return web.Response(
            text=json.dumps({"ok": ok}),
            content_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    elif request.method == "DELETE":
        body = await request.json()
        route = (body.get("route") or "").strip()
        await remove_subscription(uid, route)
        return web.Response(
            text=json.dumps({"ok": True}),
            content_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    subs = await get_user_subscriptions(uid)
    return web.Response(
        text=json.dumps({"subscriptions": subs}, ensure_ascii=False, default=str),
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


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


def _build_app_webhook(dp: Dispatcher, bot: Bot) -> web.Application:
    """Webhook mode: bot updates come via HTTP."""
    app = web.Application()
    app.router.add_get("/api/ads",           api_ads)
    app.router.add_get("/api/stats",         api_stats)
    app.router.add_get("/api/users",         api_users)
    app.router.add_post("/api/cleanup",      api_cleanup)
    app.router.add_get("/api/is_admin",      api_is_admin)
    app.router.add_get("/api/subscriptions", api_subscriptions)
    app.router.add_post("/api/subscriptions", api_subscriptions)
    app.router.add_delete("/api/subscriptions", api_subscriptions)
    webhook_path = f"/bot{Config.BOT_TOKEN}"
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)
    app.router.add_get("/",          static_file)
    app.router.add_get("/{path:.+}", static_file)
    return app


def _build_app_polling() -> web.Application:
    """Polling mode: bot updates via polling, webapp just serves UI."""
    app = web.Application()
    app.router.add_get("/api/ads",           api_ads)
    app.router.add_get("/api/stats",         api_stats)
    app.router.add_get("/api/users",         api_users)
    app.router.add_post("/api/cleanup",      api_cleanup)
    app.router.add_get("/api/is_admin",      api_is_admin)
    app.router.add_get("/api/subscriptions", api_subscriptions)
    app.router.add_post("/api/subscriptions", api_subscriptions)
    app.router.add_delete("/api/subscriptions", api_subscriptions)
    app.router.add_get("/",          static_file)
    app.router.add_get("/{path:.+}", static_file)
    return app


async def start_web_server(dp: Dispatcher, bot: Bot, webhook_mode: bool = False):
    port = int(os.environ.get("PORT", 8888))
    app  = _build_app_webhook(dp, bot) if webhook_mode else _build_app_polling()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port, reuse_address=True, reuse_port=False)
    await site.start()
    logger.info(f"Webapp server started on port {port} ✅")
    return port


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    if not Config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN .env faylda ko'rsatilmagan!")

    await init_db()

    # Seed default monitored groups
    await add_monitored_group(1411032261, "Logistika guruhi 1", 0)
    await add_monitored_group(1159400110, "Logistika guruhi 2", 0)
    await add_monitored_group(1489222508, "YUK TASHISH XIZMATLARI", 0)

    # Bot, dp, webapp all initialized together below

    # Bot
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)
    dp.include_router(subscriptions.router)
    dp.include_router(group_ai.router)
    dp.include_router(user.router)

    # Set bot globally for notifications
    _notify.set_bot(bot)

    # Background cleanup: delete ads older than 7 days every 24 hours
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(86400)
            count = await cleanup_old_ads(7)
            if count:
                logger.info(f"Auto-cleanup: {count} ta eski e'lon o'chirildi")

    asyncio.create_task(_cleanup_loop())

    # Always use polling locally — more reliable than webhook + localtunnel
    await bot.delete_webhook(drop_pending_updates=True)
    port = await start_web_server(dp, bot, webhook_mode=False)
    logger.info(f"Bot ishga tushdi (polling mode, webapp port={port})")

    tasks = [dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())]

    if Config.API_ID and Config.API_HASH:
        from handlers.group import start_userbot
        tasks.append(start_userbot())

    # Try to start localtunnel in background for external webapp access
    webapp_url = Config.WEBAPP_URL
    if webapp_url:
        subdomain = webapp_url.replace("https://", "").replace(".loca.lt", "")
        asyncio.create_task(_start_localtunnel(port, subdomain))

    await asyncio.gather(*tasks)


async def _start_localtunnel(port: int, subdomain: str):
    """No-op — tunnel is managed by start_all.py (cloudflared)."""
    logger.info("Tunnel start_all.py orqali boshqariladi")


if __name__ == "__main__":
    asyncio.run(main())
