from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from database import get_user_history, clear_user_history

router = Router(name="history_router")


@router.message(Command("history"))
@router.callback_query(F.data == "nav_history")
async def handle_view_history(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays user's recent lookup history with 1-click re-query buttons."""
    user_id = event.from_user.id
    history = await get_user_history(user_id, limit=8)

    if not history:
        text = (
            "🕒 <b>SEARCH HISTORY:</b>\n"
            "──────────────────────────────\n"
            "Your recent lookup history is currently empty.\n"
            "<i>Whenever you inspect a user, channel, or group, it will be recorded here for instant re-lookup.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")]
        ])
    else:
        text = (
            f"🕒 <b>RECENT SEARCH HISTORY ({len(history)}):</b>\n"
            "──────────────────────────────\n"
            "<i>Click any previous search to re-inspect live data:</i>"
        )
        buttons = []
        for h in history:
            icon = "👤" if h["target_type"] == "user" else ("📢" if h["target_type"] == "channel" else "👥")
            title = h["target_title"] or h["target_username"] or str(h["target_id"])
            query_val = h["target_username"] or str(h["target_id"])
            buttons.append([
                InlineKeyboardButton(
                    text=f"{icon} {title[:28]}",
                    callback_data=f"query_chat_{query_val}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(text="🗑️ Clear All History", callback_data="hist_clear"),
            InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")
        ])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "hist_clear")
async def handle_clear_history(callback: CallbackQuery):
    """Clears all history for user."""
    await clear_user_history(callback.from_user.id)
    await callback.answer("🗑️ Search history cleared!", show_alert=True)
    await handle_view_history(callback)
