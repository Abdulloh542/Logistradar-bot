import aiosqlite
from config import Config

DB = Config.DB_PATH

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                from_loc    TEXT,
                to_loc      TEXT,
                weight      TEXT,
                truck       TEXT,
                cargo       TEXT,
                price       TEXT,
                km          REAL DEFAULT 0,
                hours       REAL DEFAULT 0,
                phone       TEXT,
                link        TEXT,
                customs     TEXT DEFAULT '',
                source      TEXT DEFAULT 'Logistradar',
                group_id    INTEGER DEFAULT 0,
                message_id  INTEGER DEFAULT 0,
                raw_text    TEXT DEFAULT '',
                view_count  INTEGER DEFAULT 0,
                phone_count INTEGER DEFAULT 0,
                created     DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migrations for existing DBs
        for col, defval in [
            ("group_id",    "INTEGER DEFAULT 0"),
            ("message_id",  "INTEGER DEFAULT 0"),
            ("raw_text",    "TEXT DEFAULT ''"),
            ("view_count",  "INTEGER DEFAULT 0"),
            ("phone_count", "INTEGER DEFAULT 0"),
        ]:
            try:
                await db.execute(f"ALTER TABLE ads ADD COLUMN {col} {defval}")
            except Exception:
                pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS monitored_groups (
                group_id   INTEGER PRIMARY KEY,
                title      TEXT DEFAULT '',
                added_by   INTEGER DEFAULT 0,
                added_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_ads (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER,
                from_loc TEXT,
                to_loc   TEXT,
                weight   TEXT,
                truck    TEXT,
                cargo    TEXT,
                price    TEXT,
                phone    TEXT,
                created  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id  INTEGER PRIMARY KEY,
                lang     TEXT DEFAULT 'uz',
                truck    TEXT DEFAULT 'ALL',
                username TEXT
            )
        """)
        await db.commit()

async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row:
                return dict(row)
    return {"user_id": user_id, "lang": "uz", "truck": "ALL"}

async def save_user(user_id: int, lang: str = "uz", truck: str = "ALL", username: str = ""):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT INTO users (user_id, lang, truck, username)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang, truck=excluded.truck, username=excluded.username
        """, (user_id, lang, truck, username))
        await db.commit()

async def get_country_counts() -> dict:
    """Returns {country_keyword: count} from ads table."""
    from utils.keyboards import COUNTRIES
    counts = {}
    async with aiosqlite.connect(DB) as db:
        for name, _ in COUNTRIES:
            async with db.execute(
                "SELECT COUNT(*) FROM ads WHERE LOWER(from_loc) LIKE ? OR LOWER(to_loc) LIKE ?",
                (f"%{name.lower()}%", f"%{name.lower()}%")
            ) as cur:
                counts[name] = (await cur.fetchone())[0]
    return counts


async def get_top_directions(limit: int = 8) -> list:
    """Returns top N 'from_loc → to_loc' pairs by frequency."""
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            """SELECT from_loc||' → '||to_loc as dir, COUNT(*) as cnt
               FROM ads WHERE from_loc != '' AND to_loc != ''
               GROUP BY from_loc, to_loc ORDER BY cnt DESC LIMIT ?""",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]


async def search_ads(query: str = "", truck: str = "ALL", limit: int = 10, offset: int = 0):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        parts = query.lower().split() if query else []
        conditions = []
        params = []
        for p in parts:
            conditions.append("(LOWER(from_loc)||' '||LOWER(to_loc)||' '||LOWER(cargo)) LIKE ?")
            params.append(f"%{p}%")
        if truck and truck != "ALL":
            conditions.append("LOWER(truck) LIKE ?")
            params.append(f"%{truck.lower()}%")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.extend([limit, offset])
        async with db.execute(
            f"SELECT * FROM ads {where} ORDER BY created DESC LIMIT ? OFFSET ?", params
        ) as cur:
            rows = await cur.fetchall()
        async with db.execute(
            f"SELECT COUNT(*) FROM ads {where}", params[:-2]
        ) as cur:
            total = (await cur.fetchone())[0]
        return [dict(r) for r in rows], total

async def add_ad(data: dict):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT INTO ads (from_loc,to_loc,weight,truck,cargo,price,km,hours,phone,link,customs,source,group_id,message_id,raw_text)
            VALUES (:from_loc,:to_loc,:weight,:truck,:cargo,:price,:km,:hours,:phone,:link,:customs,:source,:group_id,:message_id,:raw_text)
        """, {
            "from_loc":   data.get("from_loc", ""),
            "to_loc":     data.get("to_loc", ""),
            "weight":     data.get("weight", ""),
            "truck":      data.get("truck", ""),
            "cargo":      data.get("cargo", ""),
            "price":      data.get("price", ""),
            "km":         data.get("km", 0),
            "hours":      data.get("hours", 0),
            "phone":      data.get("phone", ""),
            "link":       data.get("link", ""),
            "customs":    data.get("customs", ""),
            "source":     data.get("source", "Telegram"),
            "group_id":   data.get("group_id", 0),
            "message_id": data.get("message_id", 0),
            "raw_text":   data.get("raw_text", ""),
        })
        await db.commit()

async def increment_view(ad_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE ads SET view_count = view_count + 1 WHERE id=?", (ad_id,))
        await db.commit()

async def increment_phone(ad_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE ads SET phone_count = phone_count + 1 WHERE id=?", (ad_id,))
        await db.commit()

# ── Monitored groups ────────────────────────────────────────────────────────

async def add_monitored_group(group_id: int, title: str = "", added_by: int = 0):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT INTO monitored_groups (group_id, title, added_by)
            VALUES (?, ?, ?)
            ON CONFLICT(group_id) DO UPDATE SET title=excluded.title
        """, (group_id, title, added_by))
        await db.commit()

async def remove_monitored_group(group_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM monitored_groups WHERE group_id=?", (group_id,))
        await db.commit()

async def get_monitored_groups() -> list[dict]:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM monitored_groups ORDER BY added_at DESC") as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

async def get_monitored_group_ids() -> set[int]:
    groups = await get_monitored_groups()
    ids = set()
    for g in groups:
        gid = g["group_id"]
        ids.add(gid)
        # Also add with -100 prefix for supergroup format
        if gid > 0:
            ids.add(-(1000000000000 + gid) if gid > 1000000000 else -(1000000000 + gid))
            ids.add(-int(f"100{gid}"))
    return ids

async def get_user_ads(user_id: int):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_ads WHERE user_id=? ORDER BY created DESC", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

async def add_user_ad(user_id: int, data: dict):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT INTO user_ads (user_id,from_loc,to_loc,weight,truck,cargo,price,phone)
            VALUES (:user_id,:from_loc,:to_loc,:weight,:truck,:cargo,:price,:phone)
        """, {"user_id": user_id, **data})
        await db.commit()

async def delete_user_ad(ad_id: int, user_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM user_ads WHERE id=? AND user_id=?", (ad_id, user_id))
        await db.commit()

async def get_ad_by_id(ad_id: int) -> dict | None:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM ads WHERE id=?", (ad_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def get_ad_count():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*) FROM ads") as cur:
            return (await cur.fetchone())[0]
