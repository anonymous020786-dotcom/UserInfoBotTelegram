from typing import Optional, List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ui.locales import get_text
from core.directory_data import DIRECTORY_CATEGORIES


def main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Returns the primary interactive dashboard inline keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text=get_text("btn_user_lookup", lang), callback_data="nav_user_lookup"),
            InlineKeyboardButton(text=get_text("btn_channel_finder", lang), callback_data="nav_channel_finder")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_group_finder", lang), callback_data="nav_group_finder"),
            InlineKeyboardButton(text=get_text("btn_forward_inspect", lang), callback_data="nav_forward_inspect")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_directory", lang), callback_data="nav_directory"),
            InlineKeyboardButton(text=get_text("btn_tools", lang), callback_data="nav_tools")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_favorites", lang), callback_data="nav_favorites"),
            InlineKeyboardButton(text=get_text("btn_history", lang), callback_data="nav_history")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_features", lang), callback_data="nav_features"),
            InlineKeyboardButton(text=get_text("btn_settings", lang), callback_data="nav_settings")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_help", lang), callback_data="nav_help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_actions_keyboard(target_id: int, username: Optional[str], is_fav: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    """Action buttons for an inspected Telegram User."""
    fav_text = get_text("btn_remove_fav", lang) if is_fav else get_text("btn_add_fav", lang)
    fav_action = f"fav_del_{target_id}" if is_fav else f"fav_add_{target_id}"

    buttons = [
        [
            InlineKeyboardButton(text=get_text("btn_export_card", lang), callback_data=f"exp_card_{target_id}"),
            InlineKeyboardButton(text=get_text("btn_export_pdf", lang), callback_data=f"exp_pdf_{target_id}")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_export_qr", lang), callback_data=f"exp_qr_{target_id}"),
            InlineKeyboardButton(text=get_text("btn_export_vcard", lang), callback_data=f"exp_vcf_{target_id}")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_raw_json", lang), callback_data=f"exp_raw_{target_id}"),
            InlineKeyboardButton(text=fav_text, callback_data=fav_action)
        ],
        [
            InlineKeyboardButton(text="🔗 Open Profile (tg://)", url=f"tg://user?id={target_id}"),
            InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="nav_home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_actions_keyboard(chat_id: int, username: Optional[str], is_fav: bool = False, lang: str = "en", linked_chat_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Action buttons for an inspected Channel."""
    fav_text = get_text("btn_remove_fav", lang) if is_fav else get_text("btn_add_fav", lang)
    fav_action = f"fav_del_{chat_id}" if is_fav else f"fav_add_{chat_id}"

    row1 = [
        InlineKeyboardButton(text=get_text("btn_export_card", lang), callback_data=f"exp_card_{chat_id}"),
        InlineKeyboardButton(text=get_text("btn_export_pdf", lang), callback_data=f"exp_pdf_{chat_id}")
    ]
    row2 = [
        InlineKeyboardButton(text=get_text("btn_export_qr", lang), callback_data=f"exp_qr_{chat_id}"),
        InlineKeyboardButton(text=get_text("btn_raw_json", lang), callback_data=f"exp_raw_{chat_id}")
    ]
    row3 = [
        InlineKeyboardButton(text=fav_text, callback_data=fav_action)
    ]
    if username:
        row3.append(InlineKeyboardButton(text="📢 Open Channel", url=f"https://t.me/{username}"))

    row4 = []
    if linked_chat_id:
        row4.append(InlineKeyboardButton(text="💬 Linked Discussion Chat", callback_data=f"query_chat_{linked_chat_id}"))

    row5 = [InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="nav_home")]

    grid = [row1, row2, row3]
    if row4:
        grid.append(row4)
    grid.append(row5)
    return InlineKeyboardMarkup(inline_keyboard=grid)


def group_actions_keyboard(chat_id: int, username: Optional[str], is_fav: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    """Action buttons for an inspected Supergroup / Group."""
    fav_text = get_text("btn_remove_fav", lang) if is_fav else get_text("btn_add_fav", lang)
    fav_action = f"fav_del_{chat_id}" if is_fav else f"fav_add_{chat_id}"

    buttons = [
        [
            InlineKeyboardButton(text=get_text("btn_export_card", lang), callback_data=f"exp_card_{chat_id}"),
            InlineKeyboardButton(text=get_text("btn_export_pdf", lang), callback_data=f"exp_pdf_{chat_id}")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_export_qr", lang), callback_data=f"exp_qr_{chat_id}"),
            InlineKeyboardButton(text=get_text("btn_raw_json", lang), callback_data=f"exp_raw_{chat_id}")
        ],
        [
            InlineKeyboardButton(text=fav_text, callback_data=fav_action)
        ],
        [
            InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="nav_home")
        ]
    ]
    if username:
        buttons[2].append(InlineKeyboardButton(text="👥 Open Group", url=f"https://t.me/{username}"))
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def directory_categories_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Displays 12 categories grid."""
    keyboard = []
    keys = list(DIRECTORY_CATEGORIES.keys())
    for i in range(0, len(keys), 2):
        row = []
        k1 = keys[i]
        c1 = DIRECTORY_CATEGORIES[k1]
        row.append(InlineKeyboardButton(text=f"{c1['emoji']} {c1['name']}", callback_data=f"cat_{k1}_1"))
        if i + 1 < len(keys):
            k2 = keys[i + 1]
            c2 = DIRECTORY_CATEGORIES[k2]
            row.append(InlineKeyboardButton(text=f"{c2['emoji']} {c2['name']}", callback_data=f"cat_{k2}_1"))
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text=get_text("btn_roulette", lang), callback_data="dir_roulette"),
        InlineKeyboardButton(text=get_text("btn_submit_channel", lang), callback_data="dir_submit")
    ])
    keyboard.append([InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="nav_home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def directory_pagination_keyboard(category_key: str, current_page: int, total_pages: int, items: List[Dict[str, Any]], lang: str = "en") -> InlineKeyboardMarkup:
    """Paginated items list with navigation controls."""
    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{'📢' if item['type']=='channel' else '👥'} {item['title']} ({item['members']})",
                callback_data=f"query_chat_{item['username']}"
            )
        ])

    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"cat_{category_key}_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {current_page}/{total_pages}", callback_data="noop"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"cat_{category_key}_{current_page + 1}"))

    keyboard.append(nav_row)
    keyboard.append([
        InlineKeyboardButton(text="📂 All Categories", callback_data="nav_directory"),
        InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="nav_home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def settings_keyboard(current_lang: str, current_theme: str) -> InlineKeyboardMarkup:
    """Settings menu for language and presentation theme."""
    lang_flags = {
        "en": "🇺🇸 English",
        "es": "🇪🇸 Español",
        "hi": "🇮🇳 हिन्दी",
        "ru": "🇷🇺 Русский",
        "ar": "🇸🇦 العربية"
    }
    themes = {
        "cyberpunk": "⚡ Cyberpunk Neo",
        "minimalist": "🌿 Minimalist Clean",
        "osint": "🕵️ Detailed OSINT"
    }

    keyboard = []
    # Language row 1
    keyboard.append([
        InlineKeyboardButton(text=f"{'✓ ' if current_lang=='en' else ''}{lang_flags['en']}", callback_data="set_lang_en"),
        InlineKeyboardButton(text=f"{'✓ ' if current_lang=='es' else ''}{lang_flags['es']}", callback_data="set_lang_es")
    ])
    # Language row 2
    keyboard.append([
        InlineKeyboardButton(text=f"{'✓ ' if current_lang=='hi' else ''}{lang_flags['hi']}", callback_data="set_lang_hi"),
        InlineKeyboardButton(text=f"{'✓ ' if current_lang=='ru' else ''}{lang_flags['ru']}", callback_data="set_lang_ru"),
        InlineKeyboardButton(text=f"{'✓ ' if current_lang=='ar' else ''}{lang_flags['ar']}", callback_data="set_lang_ar")
    ])

    # Theme selection
    for th_key, th_name in themes.items():
        keyboard.append([
            InlineKeyboardButton(text=f"{'✓ ' if current_theme==th_key else ''}{th_name}", callback_data=f"set_theme_{th_key}")
        ])

    keyboard.append([InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def tools_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Dev and OSINT Utilities menu."""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Post Forensics & Views", callback_data="tool_post_forensics"),
            InlineKeyboardButton(text="⚖️ Channel Comparator", callback_data="tool_compare")
        ],
        [
            InlineKeyboardButton(text="💎 Fragment NFT Live", callback_data="tool_fragment"),
            InlineKeyboardButton(text="🌐 Domain & IP OSINT", callback_data="tool_domain_ip")
        ],
        [
            InlineKeyboardButton(text="📱 Phone Number OSINT", callback_data="tool_phone_osint"),
            InlineKeyboardButton(text="🔢 64-bit ID Forensics", callback_data="tool_idmath")
        ],
        [
            InlineKeyboardButton(text="🤖 Bot Token Checker", callback_data="tool_bot_check"),
            InlineKeyboardButton(text="🌐 Data Centers (DC) Map", callback_data="tool_dc_map")
        ],
        [
            InlineKeyboardButton(text="🏁 Custom QR Generator", callback_data="tool_custom_qr"),
            InlineKeyboardButton(text="🛡️ Phishing & Scam Auditor", callback_data="tool_scam_audit")
        ],
        [
            InlineKeyboardButton(text="🎨 Sticker Pack Forensics", callback_data="tool_sticker"),
            InlineKeyboardButton(text="🔗 Telegram Deep Links", callback_data="tool_deeplinks")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="nav_home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)



def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin dashboard actions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Real-time Analytics", callback_data="adm_stats"),
            InlineKeyboardButton(text="📢 Global Broadcast", callback_data="adm_broadcast")
        ],
        [
            InlineKeyboardButton(text="📥 Review Submissions", callback_data="adm_submissions"),
            InlineKeyboardButton(text="🧹 Prune Exports Dir", callback_data="adm_prune")
        ],
        [
            InlineKeyboardButton(text="🏠 Exit to Home", callback_data="nav_home")
        ]
    ])
