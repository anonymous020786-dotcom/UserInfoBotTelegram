"""
Sentinel Telegram OSINT - Phone Intelligence & Forensics Handler
Handles /phone, /phone2user, /user2phone, /phoneaudit commands and interactive callbacks.
"""
import io
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.phone_resolver import resolve_phone_to_telegram, audit_user_phone_exposure
from ui.formatters import escape_html

router = Router(name="phone_intel_router")


# ==============================================================================
# 1. PHONE NUMBER TO TELEGRAM ACCOUNT RESOLVER (/phone, /phone2user)
# ==============================================================================
@router.message(Command("phone", "phone2user", "findphone", "num2user"))
async def handle_phone_to_user_command(message: Message):
    """Inspects an international phone number and resolves Telegram identity vectors."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📱 <b>PHONE TO USER RESOLVER USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/phone &lt;international_phone_number&gt;</code>\n"
            "<i>Examples:</i>\n"
            "• <code>/phone +12025550123</code> (Standard International)\n"
            "• <code>/phone +88801234567</code> (Fragment TON Anonymous Virtual Number)\n"
            "• <code>/phone +919876543210</code> (India Mobile Number)",
            parse_mode="HTML"
        )
        return

    phone_raw = parts[1].strip()
    status_msg = await message.reply("📡 <i>Auditing phone carrier, Fragment blockchain, and Telegram protocol...</i>", parse_mode="HTML")

    try:
        res = await resolve_phone_to_telegram(phone_raw)

        lines = [
            f"📱 <b>[PHONE TO USER FORENSICS: <code>{res['formatted']}</code>]</b>",
            "──────────────────────────────",
            f"• <b>Geographic Origin:</b> {res['flag']} <b>{res['country']}</b>",
            f"• <b>Dial Prefix:</b> <code>{res['dial_code']}</code> (Timezone: <code>{res['timezone']}</code>)",
            f"• <b>Format Validity:</b> {'✅ Valid Length (E.164)' if res['is_valid_length'] else '⚠️ Irregular Length'}",
            "──────────────────────────────"
        ]

        kb_rows = []

        # If Indian Telecom Circle Info
        if res.get("india_telecom"):
            it = res["india_telecom"]
            lines.extend([
                "📡 <b>[TELECOM OPERATOR & CIRCLE ALLOCATION]</b>",
                f"• <b>Telecom Circle:</b> 📍 <b>{it['circle']}</b>",
                f"• <b>Service Provider:</b> 🏢 <b>{it['operator']}</b>",
                f"• <b>National Format:</b> <code>{it['national_format']}</code>",
                f"• <b>E.164 Spaced:</b> <code>{it['e164_spaced']}</code>",
                "──────────────────────────────"
            ])

        # If Indian Financial UPI Vectors
        if res.get("upi_data"):
            upi = res["upi_data"]
            lines.extend([
                "💳 <b>[FINANCIAL UPI OSINT VECTORS]</b>",
                f"• <b>PhonePe VPA:</b> <code>{upi['phonepe']}</code>",
                f"• <b>Paytm VPA:</b> <code>{upi['paytm']}</code>",
                f"• <b>Google Pay VPA:</b> <code>{upi['google_pay']}</code>",
                f"• <b>BHIM VPA:</b> <code>{upi['bhim']}</code>",
                "<i>💡 Tip: Copy any VPA above or tap below to reveal registered KYC name!</i>",
                "──────────────────────────────"
            ])

        # If Fragment +888 Anonymous Virtual Number
        if res["is_fragment_nft"] and res["fragment_data"]:
            frag = res["fragment_data"]
            lines.extend([
                "💎 <b>[FRAGMENT TON VIRTUAL NUMBER NFT]</b>",
                f"• <b>Marketplace Status:</b> <b>{frag['status']}</b>",
            ])
            if frag.get("price_ton"):
                lines.append(f"• <b>Valuation:</b> 💎 <b>{frag['price_ton']:,} TON</b> (~${frag.get('price_usd_est', 0):,} USD)")
            if frag.get("highest_bid"):
                lines.append(f"• <b>Highest Bid:</b> <code>{frag['highest_bid']}</code>")
            if frag.get("auction_ends"):
                lines.append(f"• <b>Auction Timer:</b> ⏳ <code>{frag['auction_ends']}</code>")
            if frag.get("owner_address"):
                lines.append(f"• <b>Owner TON Wallet:</b> <code>{frag['owner_address']}</code>")
            lines.append("──────────────────────────────")
            kb_rows.append([InlineKeyboardButton(text="💎 View on Fragment NFT", url=frag["fragment_url"])])

        # Direct Resolution Protocols
        lines.extend([
            "🔗 <b>DIRECT PROTOCOL RESOLUTION VECTORS:</b>",
            "<i>Tap buttons below to resolve profile in native Telegram:</i>\n"
        ])

        kb_rows.append([
            InlineKeyboardButton(text="✈️ Open via tg:// Protocol", url=res["tg_protocol"]),
            InlineKeyboardButton(text="🌐 Open via t.me/+", url=res["tg_web"])
        ])
        
        action_row = [InlineKeyboardButton(text="💬 WhatsApp Direct", url=res["wa_link"])]
        if res.get("upi_data"):
            action_row.append(InlineKeyboardButton(text="💳 Reveal Bank KYC Name", callback_data=f"upi_reveal_{res['digits']}"))
        kb_rows.append(action_row)

        kb_rows.append([InlineKeyboardButton(text="📥 Export .VCF Contact (Reveal Name/Photo)", callback_data=f"get_vcard_{res['digits']}")])

        # Step-by-Step Operator Guide
        lines.extend([
            "💡 <b>HOW TO REVEAL THIS USER'S NAME & PHOTO:</b>",
            "1. <b>Tap '✈️ Open via tg://'</b>: Launches private chat in Telegram desktop/mobile.",
            "2. <b>Tap '📥 Export .VCF Contact'</b>: Download & save to phone address book; Telegram immediately syncs and displays registered name & profile photo!",
            "3. <b>Tap '💳 Reveal Bank KYC Name'</b>: Query NPCI UPI network to fetch verified legal name."
        ])

        kb_rows.append([InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")])

        await status_msg.edit_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
            parse_mode="HTML"
        )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Error resolving phone number:</b> {escape_html(str(e))}\n\n"
            "Please check the phone format (e.g., <code>/phone +919876543210</code>) and try again.",
            parse_mode="HTML"
        )


# ==============================================================================
# 2. USERNAME TO PHONE EXPOSURE AUDIT (/user2phone, /phoneaudit)
# ==============================================================================
@router.message(Command("user2phone", "phoneaudit", "auditphone"))
async def handle_user_to_phone_audit_command(message: Message, bot: Bot):
    """Audits a Telegram user or channel to detect phone leaks or contact exposure."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🕵️ <b>USER TO PHONE FORENSICS USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/user2phone &lt;@username or ID&gt;</code>\n"
            "<i>Example:</i> <code>/user2phone @durov</code> or <code>/user2phone 777000</code>",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"🕵️ <i>Auditing profile text, bio, and metadata for @{target.lstrip('@')}...</i>", parse_mode="HTML")

    try:
        res = await audit_user_phone_exposure(target, bot=bot)

        if not res["found"]:
            await status_msg.edit_text(f"❌ <b>Error:</b> {res.get('error', 'Could not resolve target.')}", parse_mode="HTML")
            return

        ent = res["entity"]
        title = escape_html(ent.get("title", res["identifier"]))
        uname = ent.get("username", res["identifier"])

        lines = [
            f"🕵️ <b>[PHONE EXPOSURE AUDIT: @{uname}]</b>",
            "──────────────────────────────",
            f"• <b>Target Entity:</b> <b>{title}</b> (@{uname})",
            f"• <b>Account Classification:</b> <code>{ent.get('type', 'user').title()}</code>",
            f"• <b>Privacy Status:</b> <b>{res['rating']}</b>",
            f"• <b>Deanonymization Risk Score:</b> <b>{res['threat_score']} / 100</b>",
            "──────────────────────────────"
        ]

        kb_rows = []

        if res["extracted_phones"]:
            lines.append("🚨 <b>CLEARTEXT NUMBERS DETECTED IN BIO:</b>")
            for ph in res["extracted_phones"]:
                lines.append(f"• <code>{ph}</code>")
                kb_rows.append([InlineKeyboardButton(text=f"🔍 Audit Number {ph}", callback_data=f"audit_num_{ph.lstrip('+')}")])
            lines.append("")
        else:
            lines.extend([
                "🔒 <b>NO CLEARTEXT PHONE DETECTED:</b>",
                "• Profile description contains no exposed phone numbers or dial codes.",
                "• Phone number is securely protected by Telegram's server-side encryption.",
                ""
            ])

        if res["has_wa_link"]:
            lines.append("⚠️ <b>External Contact Vector:</b> Profile contains external WhatsApp link.")

        frag = res.get("fragment_info", {})
        if frag and frag.get("status") in ["Sold", "On Auction"]:
            lines.append(f"💎 <b>Fragment TON Collectible:</b> {frag.get('status')} (Valuation: {frag.get('price_ton', 'N/A')} TON)")

        lines.extend([
            "──────────────────────────────",
            "📋 <b>FORENSIC ASSESSMENT:</b>",
            f"<i>{res['recommendation']}</i>\n",
            "💡 <b>Mutual Contact Discovery:</b>",
            "To test if you share mutual contacts, save the target to your phone's address book and allow Telegram client sync."
        ])

        kb_rows.append([
            InlineKeyboardButton(text=f"🔍 Full OSINT Info", callback_data=f"query_chat_{uname}"),
            InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")
        ])

        await status_msg.edit_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
            parse_mode="HTML"
        )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Error auditing target:</b> {escape_html(str(e))}",
            parse_mode="HTML"
        )


# ==============================================================================
# 3. INTERACTIVE CALLBACKS (vCard Download & 1-Click Lookups)
# ==============================================================================
@router.callback_query(F.data.startswith("get_vcard_"))
async def handle_vcard_download(callback: CallbackQuery):
    """Generates and uploads downloadable .vcf contact card."""
    digits = callback.data.split("get_vcard_")[-1].strip()
    vcard_text = (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        f"FN:Sentinel Target +{digits}\r\n"
        f"TEL;TYPE=CELL:+{digits}\r\n"
        "NOTE:Exported by Sentinel OSINT Bot for Telegram Contact Discovery\r\n"
        "END:VCARD\r\n"
    )

    file_bytes = vcard_text.encode("utf-8")
    doc = BufferedInputFile(file_bytes, filename=f"contact_{digits}.vcf")

    await callback.message.reply_document(
        document=doc,
        caption=(
            f"📥 <b>vCard Contact File (+{digits})</b>\n"
            "Open this file to add the number to your mobile address book. "
            "Telegram will immediately display the account if registered!"
        ),
        parse_mode="HTML"
    )
    await callback.answer("vCard generated!")


@router.callback_query(F.data.startswith("audit_num_"))
async def handle_audit_num_callback(callback: CallbackQuery):
    """Executes 1-click phone audit from inline button."""
    digits = callback.data.split("audit_num_")[-1].strip()
    await callback.answer("Auditing number...")
    fake_msg = callback.message
    fake_msg.text = f"/phone +{digits}"
    await handle_phone_to_user_command(fake_msg)


@router.callback_query(F.data.startswith("upi_reveal_"))
async def handle_upi_reveal_callback(callback: CallbackQuery):
    """Guides operator on querying NPCI UPI network to extract bank account holder name."""
    digits = callback.data.split("upi_reveal_")[-1].strip()
    d10 = digits[-10:] if len(digits) >= 10 else digits
    await callback.answer()

    text = (
        f"💳 <b>[UPI FINANCIAL OSINT // KYC NAME REVEAL]</b>\n"
        f"<b>Target Number:</b> <code>+91 {d10}</code>\n"
        "──────────────────────────────\n"
        "In India, the NPCI UPI banking switch connects directly to the target's bank account. "
        "Any UPI app will fetch and display their verified legal KYC name before you send any money.\n\n"
        "<b>Registered VPA Handles for this number:</b>\n"
        f"• <b>PhonePe:</b> <code>{d10}@ybl</code>\n"
        f"• <b>Paytm:</b> <code>{d10}@paytm</code>\n"
        f"• <b>Google Pay:</b> <code>{d10}@oksbi</code>\n"
        f"• <b>BHIM / UPI:</b> <code>{d10}@upi</code>\n\n"
        "<b>Steps to Reveal Legal Bank Name:</b>\n"
        "1. Tap any VPA handle above to copy it.\n"
        "2. Open <b>Paytm</b>, <b>PhonePe</b>, <b>Google Pay</b>, or <b>BHIM</b>.\n"
        "3. Choose <b>'Pay to UPI ID / Mobile Number'</b> and paste the handle.\n"
        "4. The official banking interface immediately displays the <b>account holder's verified legal name</b> on your screen without completing any payment!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Download .VCF Contact", callback_data=f"get_vcard_{digits}")],
        [InlineKeyboardButton(text="🔙 Back to Target Forensics", callback_data=f"audit_num_{digits}")],
        [InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")]
    ])
    await callback.message.reply(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "tool_phone2user")
async def handle_phone2user_prompt(callback: CallbackQuery):
    """Prompts operator on how to use Phone to User Lookup."""
    text = (
        "📱 <b>PHONE NUMBER TO TELEGRAM LOOKUP</b>\n"
        "──────────────────────────────\n"
        "Send <code>/phone &lt;number&gt;</code> to analyze any international or Fragment virtual number.\n\n"
        "<b>Supported Formats:</b>\n"
        "• <code>/phone +12025550123</code> (US/Canada)\n"
        "• <code>/phone +88801234567</code> (Fragment TON NFT Anonymous Number)\n"
        "• <code>/phone +447911123456</code> (United Kingdom)\n"
        "• <code>/phone +919876543210</code> (India)\n\n"
        "<b>Forensic Capabilities:</b>\n"
        "• Carrier, Country Flag, Dial Prefix & Timezone\n"
        "• Fragment NFT Auction Status & TON Valuation\n"
        "• Instant tg:// & t.me/+ Client Protocol Resolution\n"
        "• 1-Tap Downloadable .VCF vCard for Mutual Sync Discovery\n"
        "• Telegram MTProto SHA-256 Privacy Boundary Analysis"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Tools", callback_data="nav_tools")],
        [InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "tool_user2phone")
async def handle_user2phone_prompt(callback: CallbackQuery):
    """Prompts operator on how to audit Username Phone Exposure."""
    text = (
        "🕵️ <b>TELEGRAM PROFILE PHONE EXPOSURE AUDIT</b>\n"
        "──────────────────────────────\n"
        "Send <code>/user2phone &lt;@username or ID&gt;</code> to audit contact leaks and deanonymization vectors.\n\n"
        "<b>Supported Formats:</b>\n"
        "• <code>/user2phone @username</code>\n"
        "• <code>/user2phone 777000</code>\n\n"
        "<b>Forensic Capabilities:</b>\n"
        "• Bio Cleartext Phone Number Pattern Extraction\n"
        "• WhatsApp, Viber & Tel Protocol Link Detection\n"
        "• Fragment Collectible & +888 Virtual Number Verification\n"
        "• Deanonymization Threat Rating & Privacy Score\n"
        "• Mutual Contact Sync Verification Protocol"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Tools", callback_data="nav_tools")],
        [InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
