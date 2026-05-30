"""
Admin buyruqlari — guruh ID larini boshqarish.

Buyruqlar (faqat adminlar uchun):
  /add_group <group_id> [sarlavha]   — guruh qo'shish
  /remove_group <group_id>           — guruh o'chirish
  /list_groups                       — barcha guruhlar ro'yxati
  /sync_groups                       — ikki sinov guruhini qo'shish (birinchi ishga tushirganda)
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import Config
from utils.db import add_monitored_group, remove_monitored_group, get_monitored_groups

logger = logging.getLogger(__name__)
router = Router()

DEFAULT_GROUPS = [
    {"id": 1411032261, "title": "Logistika guruhi 1"},
    {"id": 1159400110, "title": "Logistika guruhi 2"},
]


def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS


@router.message(Command("add_group"))
async def cmd_add_group(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Sizda ruxsat yo'q.")
        return

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 2:
        await msg.answer("❌ Foydalanish: /add_group <group_id> [sarlavha]")
        return

    raw = parts[1].lstrip("-")
    if not raw.isdigit():
        await msg.answer("❌ group_id raqam bo'lishi kerak.")
        return

    group_id = int(raw)
    title    = parts[2] if len(parts) > 2 else f"Guruh {group_id}"

    await add_monitored_group(group_id, title, msg.from_user.id)
    await msg.answer(f"✅ Guruh qo'shildi:\n<b>{title}</b>\nID: <code>{group_id}</code>")
    logger.info(f"Admin {msg.from_user.id} added group {group_id}")


@router.message(Command("remove_group"))
async def cmd_remove_group(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Sizda ruxsat yo'q.")
        return

    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("❌ Foydalanish: /remove_group <group_id>")
        return

    raw = parts[1].lstrip("-")
    if not raw.isdigit():
        await msg.answer("❌ group_id raqam bo'lishi kerak.")
        return

    group_id = int(raw)
    await remove_monitored_group(group_id)
    await msg.answer(f"🗑 Guruh o'chirildi: <code>{group_id}</code>")
    logger.info(f"Admin {msg.from_user.id} removed group {group_id}")


@router.message(Command("list_groups"))
async def cmd_list_groups(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Sizda ruxsat yo'q.")
        return

    groups = await get_monitored_groups()
    if not groups:
        await msg.answer("📭 Hech qanday guruh kuzatilmayapti.\n\n"
                         "Qo'shish: /add_group &lt;group_id&gt; [sarlavha]")
        return

    lines = [f"📋 <b>Kuzatilayotgan guruhlar ({len(groups)} ta):</b>\n"]
    for g in groups:
        added = str(g.get("added_at", ""))[:10]
        lines.append(f"• <b>{g['title']}</b>\n"
                     f"  ID: <code>{g['group_id']}</code> | {added}")

    await msg.answer("\n".join(lines))


@router.message(Command("sync_groups"))
async def cmd_sync_groups(msg: Message):
    """Sinov guruhlari: 1411032261 va 1159400110 ni qo'shadi."""
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Sizda ruxsat yo'q.")
        return

    for g in DEFAULT_GROUPS:
        await add_monitored_group(g["id"], g["title"], msg.from_user.id)

    await msg.answer(
        "✅ Sinov guruhlari qo'shildi:\n\n"
        "• <code>1411032261</code> — Logistika guruhi 1\n"
        "• <code>1159400110</code> — Logistika guruhi 2\n\n"
        "Boshqa guruh qo'shish: /add_group &lt;id&gt; &lt;nomi&gt;"
    )
