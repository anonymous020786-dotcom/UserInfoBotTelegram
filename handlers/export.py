import json
import aiohttp
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile

from core.telegram_discovery import resolve_full_entity
from core.card_generator import create_identity_card
from core.pdf_generator import generate_osint_pdf
from core.qr_generator import generate_styled_qr
from core.vcard_generator import generate_vcard
from config import AVATARS_DIR, EXPORTS_DIR

router = Router(name="export_router")


async def _download_avatar_if_available(data: dict, bot: Bot) -> Path | None:
    """Downloads profile avatar to disk for rendering in ID card."""
    target_id = data["id"]
    dest_path = AVATARS_DIR / f"avatar_{target_id}.jpg"
    if dest_path.exists():
        return dest_path

    # Try bot API file_id
    if data.get("photo_file_id") and bot:
        try:
            file = await bot.get_file(data["photo_file_id"])
            await bot.download_file(file.file_path, destination=dest_path)
            return dest_path
        except Exception:
            pass

    # Try photo_url CDN
    if data.get("photo_url"):
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(data["photo_url"]) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        with open(dest_path, "wb") as f:
                            f.write(content)
                        return dest_path
        except Exception:
            pass

    return None


@router.callback_query(F.data.startswith("exp_card_"))
async def handle_export_id_card(callback: CallbackQuery, bot: Bot):
    """Generates high-res digital ID Card PNG and sends it."""
    target_id = callback.data.replace("exp_card_", "")
    await callback.answer("🎨 Rendering Sentinel Graphic ID Card...")

    data = await resolve_full_entity(target_id, bot=bot)
    if not data:
        await callback.message.answer(f"❌ Failed to fetch data for ID Card generation ({target_id}).")
        return

    avatar_path = await _download_avatar_if_available(data, bot)
    card_path = create_identity_card(
        entity_id=data["id"],
        title=data.get("title") or "Unknown Entity",
        username=data.get("username"),
        entity_type=data.get("type", "user"),
        reg_estimate=data.get("reg_info", {}).get("estimated_month", "Unknown"),
        dc_info=f"{data.get('dc_info', {}).get('flag', '')} {data.get('dc_info', {}).get('name', 'Cloud')}",
        is_premium=data.get("is_premium", False),
        is_verified=data.get("is_verified", False),
        is_scam=data.get("is_scam", False),
        avatar_path=avatar_path
    )

    caption = (
        f"🪪 <b>SENTINEL DIGITAL IDENTITY CARD</b>\n"
        f"• <b>Target:</b> {data.get('title')}\n"
        f"• <b>Telegram ID:</b> <code>{data['id']}</code>\n"
        f"• <b>Auth Status:</b> Verified OSINT Dossier"
    )
    await callback.message.reply_photo(photo=FSInputFile(str(card_path)), caption=caption, parse_mode="HTML")


@router.callback_query(F.data.startswith("exp_pdf_"))
async def handle_export_pdf(callback: CallbackQuery, bot: Bot):
    """Generates comprehensive OSINT Dossier PDF."""
    target_id = callback.data.replace("exp_pdf_", "")
    await callback.answer("📄 Compiling PDF Intelligence Dossier...")

    data = await resolve_full_entity(target_id, bot=bot)
    if not data:
        await callback.message.answer("❌ Could not compile dossier.")
        return

    dc_str = f"{data.get('dc_info', {}).get('flag', '')} {data.get('dc_info', {}).get('name', 'Cloud')} ({data.get('dc_info', {}).get('location', '')})"
    reg_str = f"{data.get('reg_info', {}).get('estimated_month', '')} ({data.get('reg_info', {}).get('relative_age', '')})"

    extra_details = {
        "is_premium": data.get("is_premium", False),
        "is_verified": data.get("is_verified", False),
        "is_scam": data.get("is_scam", False),
        "links": data.get("osint_analysis", {}).get("links", []),
        "mentions": data.get("osint_analysis", {}).get("mentions", []),
        "language_script": data.get("osint_analysis", {}).get("language_script", "")
    }

    pdf_path = generate_osint_pdf(
        entity_id=data["id"],
        title=data.get("title", ""),
        username=data.get("username"),
        entity_type=data.get("type", "user"),
        reg_estimate=reg_str,
        dc_info=dc_str,
        bio=data.get("bio") or data.get("description"),
        extra_details=extra_details
    )

    caption = f"📄 <b>OSINT Dossier Generated for:</b> {data.get('title')}"
    await callback.message.reply_document(document=FSInputFile(str(pdf_path)), caption=caption, parse_mode="HTML")


@router.callback_query(F.data.startswith("exp_qr_"))
async def handle_export_qr(callback: CallbackQuery, bot: Bot):
    """Generates custom Telegram QR code."""
    target_id = callback.data.replace("exp_qr_", "")
    await callback.answer("🏁 Generating QR Code...")

    data = await resolve_full_entity(target_id, bot=bot)
    username = data.get("username") if data else None
    qr_data = f"https://t.me/{username}" if username else f"tg://user?id={target_id}"

    qr_path = generate_styled_qr(qr_data, filename_prefix=f"entity_{target_id}")
    caption = f"🏁 <b>Telegram QR Code:</b> <code>{qr_data}</code>"
    await callback.message.reply_photo(photo=FSInputFile(str(qr_path)), caption=caption, parse_mode="HTML")


@router.callback_query(F.data.startswith("exp_vcf_"))
async def handle_export_vcf(callback: CallbackQuery, bot: Bot):
    """Generates phone contact card (.vcf)."""
    target_id = callback.data.replace("exp_vcf_", "")
    await callback.answer("📇 Exporting vCard...")

    data = await resolve_full_entity(target_id, bot=bot)
    if not data:
        await callback.message.answer("❌ Could not generate vCard.")
        return

    vcf_path = generate_vcard(
        user_id=data["id"],
        first_name=data.get("first_name") or data.get("title") or "Telegram",
        last_name=data.get("last_name"),
        username=data.get("username"),
        bio=data.get("bio")
    )
    caption = f"📇 <b>vCard Contact:</b> Import directly to phonebook."
    await callback.message.reply_document(document=FSInputFile(str(vcf_path)), caption=caption, parse_mode="HTML")


@router.callback_query(F.data.startswith("exp_raw_"))
async def handle_export_raw(callback: CallbackQuery, bot: Bot):
    """Dumps raw JSON object of entity."""
    target_id = callback.data.replace("exp_raw_", "")
    await callback.answer("🧩 Extracting Raw JSON...")

    data = await resolve_full_entity(target_id, bot=bot)
    if not data:
        await callback.message.answer("❌ Could not extract JSON.")
        return

    json_str = json.dumps(data, indent=2, default=str)
    if len(json_str) < 3800:
        await callback.message.reply(f"🧩 <b>RAW JSON DATA:</b>\n<pre><code class=\"language-json\">{json_str}</code></pre>", parse_mode="HTML")
    else:
        # Save to file
        json_path = EXPORTS_DIR / f"raw_{target_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        await callback.message.reply_document(
            document=FSInputFile(str(json_path)),
            caption=f"🧩 <b>Full Raw JSON Dump ({target_id})</b>",
            parse_mode="HTML"
        )
