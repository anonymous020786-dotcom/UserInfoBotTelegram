from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from core.directory_data import DIRECTORY_CATEGORIES, get_category_items, get_random_item
from core.telegram_discovery import resolve_full_entity
from ui.keyboards import directory_categories_keyboard, directory_pagination_keyboard, channel_actions_keyboard, group_actions_keyboard
from ui.formatters import format_channel_report, format_group_report
from database import is_favorite

router = Router(name="directory_router")


@router.message(Command("directory"))
@router.callback_query(F.data == "nav_directory")
async def handle_directory_menu(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays 12-category community catalog."""
    text = (
        "📂 <b>SENTINEL CURATED COMMUNITY DIRECTORY</b>\n"
        "──────────────────────────────\n"
        "Browse hundreds of top-tier, verified Telegram channels and groups across 12 specialized topics.\n\n"
        "👇 <i>Select a category to browse:</i>"
    )
    kb = directory_categories_keyboard(user_lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("cat_"))
async def handle_category_page(callback: CallbackQuery, user_lang: str = "en"):
    """Handles pagination through items in a specific category."""
    parts = callback.data.split("_")
    # format: cat_<category_key>_<page>
    if len(parts) >= 3:
        cat_key = parts[1]
        try:
            page = int(parts[2])
        except ValueError:
            page = 1
    else:
        await callback.answer()
        return

    data = get_category_items(cat_key, page=page, page_size=4)
    cat_info = data["category_info"]

    text = (
        f"{cat_info['emoji']} <b>{cat_info['name'].upper()}</b>\n"
        f"──────────────────────────────\n"
        f"Displaying curated channels & groups (Page {data['current_page']} of {data['total_pages']}):\n"
        "<i>Click any community below for live inspection & stats:</i>"
    )

    kb = directory_pagination_keyboard(cat_key, data["current_page"], data["total_pages"], data["items"], user_lang)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "dir_roulette")
async def handle_directory_roulette(callback: CallbackQuery, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Discovers a random channel or group from the curated directory with live stats."""
    await callback.answer("🎲 Spinning community roulette...")
    item = get_random_item()
    data = await resolve_full_entity(item["username"], bot=bot)
    if not data:
        data = {
            "id": abs(hash(item["username"])) % 1000000000,
            "title": item["title"],
            "username": item["username"],
            "description": item["description"],
            "type": item["type"],
            "members_count": None,
            "dc_info": {},
            "reg_info": {},
            "osint_analysis": {}
        }

    fav = await is_favorite(callback.from_user.id, data["id"])
    if data["type"] == "channel":
        report = format_channel_report(data, theme=user_theme)
        kb = channel_actions_keyboard(data["id"], data.get("username"), is_fav=fav, lang=user_lang)
    else:
        report = format_group_report(data, theme=user_theme)
        kb = group_actions_keyboard(data["id"], data.get("username"), is_fav=fav, lang=user_lang)

    await callback.message.answer(
        f"🎰 <b>ROULETTE DISCOVERY:</b>\n{report}",
        reply_markup=kb,
        parse_mode="HTML"
    )
