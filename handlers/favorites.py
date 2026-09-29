from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from database import add_favorite, remove_favorite, get_favorites, is_favorite
from core.telegram_discovery import resolve_full_entity

router = Router(name="favorites_router")


@router.message(Command("favorites", "bookmarks", "favs"))
@router.callback_query(F.data == "nav_favorites")
async def handle_view_favorites(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays user's bookmarked users, channels, and groups."""
    user_id = event.from_user.id
    favs = await get_favorites(user_id)

    if not favs:
        text = (
            "⭐ <b>MY BOOKMARKS:</b>\n"
            "──────────────────────────────\n"
            "You have no saved favorites yet!\n"
            "<i>Click '⭐ Bookmark' on any user, channel, or group inspection card to save it for 1-click quick access.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")]
        ])
    else:
        text = (
            f"⭐ <b>MY BOOKMARKS ({len(favs)}):</b>\n"
            "──────────────────────────────\n"
            "<i>Click any entity below to view its live statistics:</i>"
        )
        buttons = []
        for f in favs:
            icon = "👤" if f["target_type"] == "user" else ("📢" if f["target_type"] == "channel" else "👥")
            title = f["target_title"] or f["target_username"] or str(f["target_id"])
            buttons.append([
                InlineKeyboardButton(
                    text=f"{icon} {title[:25]}",
                    callback_data=f"query_chat_{f['target_id']}"
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=f"fav_del_{f['target_id']}"
                )
            ])
        buttons.append([InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("fav_add_"))
async def handle_add_favorite(callback: CallbackQuery, bot: Bot):
    """Adds entity to personal favorites."""
    target_id_str = callback.data.replace("fav_add_", "")
    try:
        target_id = int(target_id_str)
    except ValueError:
        target_id = abs(hash(target_id_str))

    data = await resolve_full_entity(str(target_id), bot=bot)
    title = data.get("title", "Unknown") if data else "Saved Entity"
    uname = data.get("username") if data else None
    etype = data.get("type", "user") if data else "user"

    success = await add_favorite(
        user_id=callback.from_user.id,
        target_id=target_id,
        target_username=uname,
        target_title=title,
        target_type=etype
    )

    if success:
        await callback.answer("⭐ Added to your favorites!", show_alert=False)
    else:
        await callback.answer("Already in your favorites!", show_alert=False)


@router.callback_query(F.data.startswith("fav_del_"))
async def handle_del_favorite(callback: CallbackQuery):
    """Removes entity from favorites."""
    target_id_str = callback.data.replace("fav_del_", "")
    try:
        target_id = int(target_id_str)
    except ValueError:
        target_id = abs(hash(target_id_str))

    await remove_favorite(callback.from_user.id, target_id)
    await callback.answer("❌ Removed from favorites.", show_alert=False)
