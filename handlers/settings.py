from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from ui.keyboards import settings_keyboard
from ui.locales import get_text
from database import update_user_preference

router = Router(name="settings_router")


@router.message(Command("settings"))
@router.callback_query(F.data == "nav_settings")
async def handle_settings_menu(event: Message | CallbackQuery, user_lang: str = "en", user_theme: str = "cyberpunk"):
    """Displays settings panel for language and UI theme."""
    text = (
        "⚙️ <b>SENTINEL PREFERENCES & CONFIGURATION</b>\n"
        "──────────────────────────────\n"
        f"• <b>Current Interface Language:</b> <code>{user_lang.upper()}</code>\n"
        f"• <b>Active Report Style Theme:</b> <code>{user_theme.capitalize()}</code>\n\n"
        "<i>Click below to switch language or change output appearance:</i>"
    )
    kb = settings_keyboard(user_lang, user_theme)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("set_lang_"))
async def handle_change_language(callback: CallbackQuery, user_theme: str = "cyberpunk"):
    """Updates user's preferred language."""
    new_lang = callback.data.replace("set_lang_", "")
    await update_user_preference(callback.from_user.id, language=new_lang)
    confirm_msg = get_text("lang_changed", new_lang)
    await callback.answer(confirm_msg, show_alert=True)
    await handle_settings_menu(callback, user_lang=new_lang, user_theme=user_theme)


@router.callback_query(F.data.startswith("set_theme_"))
async def handle_change_theme(callback: CallbackQuery, user_lang: str = "en"):
    """Updates user's preferred visual theme."""
    new_theme = callback.data.replace("set_theme_", "")
    await update_user_preference(callback.from_user.id, theme=new_theme)
    confirm_msg = get_text("theme_changed", user_lang, theme=new_theme.capitalize())
    await callback.answer(confirm_msg, show_alert=True)
    await handle_settings_menu(callback, user_lang=user_lang, user_theme=new_theme)
