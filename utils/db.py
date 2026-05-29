import aiosqlite
from config import Config

DB = Config.DB_PATH

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                from_loc TEXT,
                to_loc   TEXT,
                weight   TEXT,
                truck    TEXT,
                cargo    TEXT,
                price    TEXT,
                km       REAL DEFAULT 0,
                hours    REAL DEFAULT 0,
                phone    TEXT,
                link     TEXT,
                customs  TEXT DEFAULT '',
                source   TEXT DEFAULT 'Logistradar',
                created  DATETIME DEFAULT CURRENT_TIMESTAMP
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
            INSERT INTO ads (from_loc,to_loc,weight,truck,cargo,price,km,hours,phone,link,customs,source)
            VALUES (:from_loc,:to_loc,:weight,:truck,:cargo,:price,:km,:hours,:phone,:link,:customs,:source)
        """, data)
        await db.commit()

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
