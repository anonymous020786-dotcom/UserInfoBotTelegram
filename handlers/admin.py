import os
import shutil
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_IDS, EXPORTS_DIR, AVATARS_DIR
from database import get_bot_stats, get_pending_submissions
from ui.keyboards import admin_panel_keyboard
import aiosqlite
from config import DB_PATH

router = Router(name="admin_router")


def is_admin(user_id: int) -> bool:
    """Checks if user ID is in authorized admin list."""
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def handle_admin_panel(message: Message):
    """Renders administrative dashboard."""
    if not is_admin(message.from_user.id):
        await message.reply("⛔ <b>Unauthorized:</b> Administrator access required.", parse_mode="HTML")
        return

    text = (
        "🛡️ <b>SENTINEL CONTROL PANEL // OPERATOR INTERFACE</b>\n"
        "──────────────────────────────\n"
        "Manage global broadcasts, review community submissions, monitor infrastructure metrics, and prune disk caches."
    )
    await message.reply(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")


@router.message(Command("stats"))
@router.callback_query(F.data == "adm_stats")
async def handle_admin_stats(event: Message | CallbackQuery):
    """Displays real-time database and performance metrics."""
    user_id = event.from_user.id
    if not is_admin(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access Denied", show_alert=True)
        return

    stats = await get_bot_stats()
    db_size_kb = DB_PATH.stat().st_size / 1024 if DB_PATH.exists() else 0
    exports_count = len(list(EXPORTS_DIR.glob("*"))) if EXPORTS_DIR.exists() else 0

    text = [
        "📊 <b>SENTINEL SYSTEM & DATABASE METRICS</b>",
        "──────────────────────────────",
        f"• <b>Total Registered Users:</b> <code>{stats['total_users']:,}</code>",
        f"• <b>Total Queries Executed:</b> <code>{stats['total_searches']:,}</code>",
        f"• <b>Saved Bookmarks:</b> <code>{stats['total_favorites']:,}</code>",
        f"• <b>Approved Submissions:</b> <code>{stats['approved_submissions']:,}</code>",
        f"• <b>Pending Submissions:</b> <code>{stats['pending_submissions']:,}</code>",
        "──────────────────────────────",
        "💾 <b>STORAGE & CACHE FOOTPRINT:</b>",
        f"• <b>Database Size:</b> <code>{db_size_kb:.2f} KB</code>",
        f"• <b>Cached Export Files:</b> <code>{exports_count} files</code>",
    ]
    report = "\n".join(text)

    if isinstance(event, CallbackQuery):
        await event.message.answer(report, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(report, parse_mode="HTML")


@router.message(Command("broadcast"))
@router.callback_query(F.data == "adm_broadcast")
async def handle_broadcast_prompt(event: Message | CallbackQuery, bot: Bot):
    """Prompts or executes global message broadcast to all users."""
    if not is_admin(event.from_user.id):
        return

    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "📢 <b>GLOBAL BROADCAST:</b>\n"
            "To send a broadcast announcement, use:\n"
            "<code>/broadcast &lt;HTML formatted announcement&gt;</code>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/broadcast &lt;announcement text&gt;</code>", parse_mode="HTML")
        return

    broadcast_text = parts[1].strip()
    status_msg = await event.reply("📡 <i>Starting broadcast dispatch...</i>", parse_mode="HTML")

    # Fetch all user IDs from DB
    user_ids = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            user_ids = [r[0] for r in rows]

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, broadcast_text, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)  # Telegram API broadcast throttle
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast Completed!</b>\n"
        f"• <b>Delivered:</b> <code>{sent}</code>\n"
        f"• <b>Failed / Blocked:</b> <code>{failed}</code>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_prune")
async def handle_prune_cache(callback: CallbackQuery):
    """Removes temporary export files to reclaim disk space."""
    if not is_admin(callback.from_user.id):
        return

    count = 0
    for p in EXPORTS_DIR.glob("*"):
        try:
            p.unlink()
            count += 1
        except Exception:
            pass

    await callback.answer(f"🧹 Pruned {count} temporary export files.", show_alert=True)
