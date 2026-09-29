from aiogram import Router, Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton

from core.telegram_discovery import search_real_telegram_entities, resolve_full_entity
from ui.formatters import format_user_report, format_channel_report, format_group_report

router = Router(name="inline_mode_router")


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, bot: Bot):
    """
    Handles inline queries (@YourBot <query>) allowing instant live search
    and inspection directly inside any chat or channel.
    """
    query = inline_query.query.strip()
    results = []

    if not query:
        # Default prompt preview
        results.append(
            InlineQueryResultArticle(
                id="default_prompt",
                title="🔍 Sentinel OSINT Search",
                description="Type any @username, ID, or keyword (e.g. @bot durov or @bot python)",
                input_message_content=InputTextMessageContent(
                    message_text="🛰️ <b>Sentinel OSINT Finder:</b> Use <code>@YourBot &lt;query&gt;</code> to inspect entities inline!",
                    parse_mode="HTML"
                )
            )
        )
        await inline_query.answer(results, cache_time=5, is_personal=True)
        return

    # Check if query is a single specific handle or ID
    clean_handle = query.lstrip("@").strip()
    is_direct_handle = len(clean_handle.split()) == 1 and len(clean_handle) >= 3

    if is_direct_handle:
        entity_data = await resolve_full_entity(clean_handle, bot=bot)
        if entity_data:
            etype = entity_data.get("type", "user")
            if etype == "channel":
                text = format_channel_report(entity_data)
            elif etype in ["group", "supergroup"]:
                text = format_group_report(entity_data)
            else:
                text = format_user_report(entity_data)

            thumb = entity_data.get("photo_url")
            results.append(
                InlineQueryResultArticle(
                    id=f"direct_{entity_data['id']}",
                    title=f"{'📢' if etype=='channel' else ('👥' if etype in ['group', 'supergroup'] else '👤')} {entity_data.get('title')}",
                    description=f"{etype.capitalize()} • {entity_data.get('username') or entity_data['id']}",
                    thumbnail_url=thumb,
                    input_message_content=InputTextMessageContent(message_text=text, parse_mode="HTML", disable_web_page_preview=True),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔗 Open Entity", url=f"https://t.me/{entity_data.get('username') or ''}")]
                    ]) if entity_data.get("username") else None
                )
            )

    # Also search keyword discoveries
    search_hits = await search_real_telegram_entities(query, limit=5, bot=bot)
    for hit in search_hits:
        if any(r.id == f"hit_{hit.get('username')}" for r in results):
            continue

        htype = hit.get("type", "channel")
        icon = "📢" if htype == "channel" else ("👥" if htype in ["group", "supergroup"] else "👤")
        uname = hit.get("username", "")
        members = hit.get("members_count")
        members_str = f" • {members:,} members" if members else ""

        results.append(
            InlineQueryResultArticle(
                id=f"hit_{uname}",
                title=f"{icon} {hit.get('title')}",
                description=f"@{uname}{members_str} • {hit.get('description', '')[:50]}",
                thumbnail_url=hit.get("photo_url"),
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"{icon} <b>{hit.get('title')}</b> (@{uname})\n"
                        f"──────────────────────────────\n"
                        f"• <b>Type:</b> {htype.capitalize()}\n"
                        f"• <b>Stats:</b> {hit.get('extra') or 'N/A'}\n"
                        f"• <b>Description:</b>\n<blockquote>{hit.get('description', 'N/A')}</blockquote>\n\n"
                        f"🔗 <a href=\"https://t.me/{uname}\">https://t.me/{uname}</a>"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"Open @{uname}", url=f"https://t.me/{uname}")]
                ])
            )
        )

    await inline_query.answer(results[:10], cache_time=10, is_personal=False)
