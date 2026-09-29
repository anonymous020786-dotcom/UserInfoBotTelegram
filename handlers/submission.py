from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from database import submit_community, update_submission_status
from core.directory_data import DIRECTORY_CATEGORIES
from config import ADMIN_IDS

router = Router(name="submission_router")


@router.message(Command("submit"))
@router.callback_query(F.data == "dir_submit")
async def handle_submit_prompt(event: Message | CallbackQuery):
    """Instructions on submitting a new community."""
    text = (
        "➕ <b>COMMUNITY SUBMISSION:</b>\n"
        "──────────────────────────────\n"
        "To submit a channel or group for inclusion in our curated directory, use this command syntax:\n\n"
        "<code>/submit &lt;category&gt; &lt;@username_or_link&gt; &lt;title &amp; description&gt;</code>\n\n"
        "<b>Available Categories:</b>\n"
        f"<code>{', '.join(DIRECTORY_CATEGORIES.keys())}</code>\n\n"
        "<i>Example:</i>\n"
        "<code>/submit coding_dev @Python Weekly tutorials and code tips</code>"
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML")


@router.message(Command("submit"))
async def handle_submit_command(message: Message, bot: Bot):
    """Processes community submission and notifies admins."""
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await handle_submit_prompt(message)
        return

    category = parts[1].lower().strip()
    link = parts[2].strip()
    desc = parts[3].strip()

    if category not in DIRECTORY_CATEGORIES:
        await message.reply(
            f"❌ Unknown category '<code>{category}</code>'.\n"
            f"Available: <code>{', '.join(DIRECTORY_CATEGORIES.keys())}</code>",
            parse_mode="HTML"
        )
        return

    sub_id = await submit_community(
        submitted_by=message.from_user.id,
        category=category,
        link=link,
        title=link,
        description=desc
    )

    await message.reply(
        "✅ <b>Submission Received!</b>\n"
        f"Your entry (ID #{sub_id}) has been forwarded to our moderation review queue. Thank you for contributing!",
        parse_mode="HTML"
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            admin_text = (
                f"📥 <b>NEW DIRECTORY SUBMISSION (#{sub_id})</b>\n"
                f"• <b>Submitter:</b> <code>{message.from_user.id}</code> (@{message.from_user.username or 'none'})\n"
                f"• <b>Category:</b> <code>{category}</code>\n"
                f"• <b>Target:</b> <code>{link}</code>\n"
                f"• <b>Description:</b> <i>{desc}</i>"
            )
            admin_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve", callback_data=f"sub_app_{sub_id}"),
                    InlineKeyboardButton(text="❌ Reject", callback_data=f"sub_rej_{sub_id}")
                ]
            ])
            await bot.send_message(admin_id, admin_text, reply_markup=admin_kb, parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("sub_app_"))
async def handle_sub_approve(callback: CallbackQuery):
    """Admin callback to approve submission."""
    sub_id = int(callback.data.replace("sub_app_", ""))
    await update_submission_status(sub_id, "approved")
    await callback.message.edit_text(
        f"{callback.message.text}\n\n<b>STATUS: APPROVED ✅</b>",
        parse_mode="HTML"
    )
    await callback.answer("Approved!")


@router.callback_query(F.data.startswith("sub_rej_"))
async def handle_sub_reject(callback: CallbackQuery):
    """Admin callback to reject submission."""
    sub_id = int(callback.data.replace("sub_rej_", ""))
    await update_submission_status(sub_id, "rejected")
    await callback.message.edit_text(
        f"{callback.message.text}\n\n<b>STATUS: REJECTED ❌</b>",
        parse_mode="HTML"
    )
    await callback.answer("Rejected.")
