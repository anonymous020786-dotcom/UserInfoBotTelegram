import os
import io
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import qrcode

from config import EXPORTS_DIR


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Loads Segoe UI font or fallback."""
    font_names = ["segoeuib.ttf" if bold else "segoeui.ttf", "arialbd.ttf" if bold else "arial.ttf"]
    for fn in font_names:
        win_path = Path("C:/Windows/Fonts") / fn
        if win_path.exists():
            try:
                return ImageFont.truetype(str(win_path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_identity_card(
    entity_id: int,
    title: str,
    username: Optional[str],
    entity_type: str,
    reg_estimate: str,
    dc_info: str,
    is_premium: bool = False,
    is_verified: bool = False,
    is_scam: bool = False,
    avatar_path: Optional[Path] = None
) -> Path:
    """
    Renders an ultra-sleek, high-res Dark-Tech / Cyberpunk digital ID card.
    Dimensions: 1080 x 600 px.
    """
    WIDTH, HEIGHT = 1080, 600
    card = Image.new("RGBA", (WIDTH, HEIGHT), (11, 15, 25, 255))
    draw = ImageDraw.Draw(card)

    # 1. Subtle Background Grid & Glow Accents
    # Top neon gradient accent bar
    for x in range(WIDTH):
        r = int(0 + (124 - 0) * (x / WIDTH))
        g = int(229 + (58 - 229) * (x / WIDTH))
        b = int(255 + (237 - 255) * (x / WIDTH))
        draw.line([(x, 0), (x, 5)], fill=(r, g, b, 255))

    # Inner Glassmorphic Border
    draw.rounded_rectangle(
        [(20, 20), (WIDTH - 20, HEIGHT - 20)],
        radius=24,
        outline=(30, 41, 59, 255),
        width=2
    )

    # Header section
    font_brand = _get_font(20, bold=True)
    draw.text((50, 45), "SENTINEL // TELEGRAM OSINT VERIFIED DOSSIER", fill=(148, 163, 184, 255), font=font_brand)
    draw.text((WIDTH - 240, 45), f"DATE: {datetime.date.today().isoformat()}", fill=(100, 116, 139, 255), font=_get_font(18))

    # Subtle horizontal line
    draw.line([(50, 80), (WIDTH - 50, 80)], fill=(30, 41, 59, 255), width=1)

    # 2. Avatar Rendering (Circular with Glowing Ring)
    avatar_size = 180
    avatar_x, avatar_y = 60, 110

    # Ring glow
    ring_box = [(avatar_x - 6, avatar_y - 6), (avatar_x + avatar_size + 6, avatar_y + avatar_size + 6)]
    draw.ellipse(ring_box, outline=(0, 229, 255, 200), width=4)

    # Create / Process avatar
    if avatar_path and Path(avatar_path).exists():
        try:
            with Image.open(avatar_path) as av_img:
                av_img = av_img.convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                card.paste(av_img, (avatar_x, avatar_y), mask)
        except Exception:
            avatar_path = None

    if not avatar_path or not Path(avatar_path).exists():
        # Fallback stylized avatar
        av_fill = (24, 34, 53, 255)
        draw.ellipse([(avatar_x, avatar_y), (avatar_x + avatar_size, avatar_y + avatar_size)], fill=av_fill)
        initials = (title[:2] if title else "TG").upper()
        draw.text((avatar_x + 55, avatar_y + 60), initials, fill=(0, 229, 255, 255), font=_get_font(52, bold=True))

    # 3. Main Entity Information
    info_x = 280
    font_title = _get_font(38, bold=True)
    clean_title = (title[:30] + '..') if len(title) > 30 else title
    draw.text((info_x, 110), clean_title, fill=(255, 255, 255, 255), font=font_title)

    # Username or Handle
    font_user = _get_font(22)
    handle_text = f"@{username}" if username else "NO PUBLIC USERNAME"
    handle_color = (56, 189, 248, 255) if username else (148, 163, 184, 255)
    draw.text((info_x, 160), handle_text, fill=handle_color, font=font_user)

    # Status Badges Bar
    badge_x = info_x
    badge_y = 200

    def draw_badge(bx: int, text: str, bg_color: tuple, text_color: tuple = (255, 255, 255)) -> int:
        b_font = _get_font(16, bold=True)
        bbox = b_font.getbbox(text)
        w = (bbox[2] - bbox[0]) + 24
        h = 30
        draw.rounded_rectangle([(bx, badge_y), (bx + w, badge_y + h)], radius=8, fill=bg_color)
        draw.text((bx + 12, badge_y + 6), text, fill=text_color, font=b_font)
        return bx + w + 12

    badge_x = draw_badge(badge_x, entity_type.upper(), (30, 41, 59))
    if is_verified:
        badge_x = draw_badge(badge_x, "VERIFIED ✓", (14, 165, 233))
    if is_premium:
        badge_x = draw_badge(badge_x, "PREMIUM ★", (168, 85, 247))
    if is_scam:
        badge_x = draw_badge(badge_x, "SCAM ALERT ⚠", (225, 29, 72))
    else:
        badge_x = draw_badge(badge_x, "CLEAN / SAFE", (16, 185, 129))

    # 4. Detailed OSINT Data Grid
    grid_y = 265
    draw.line([(50, 250), (WIDTH - 50, 250)], fill=(30, 41, 59, 255), width=1)

    labels = [
        ("TELEGRAM ID", str(entity_id)),
        ("REGISTRATION AGE", reg_estimate),
        ("DATA CENTER (DC)", dc_info),
        ("ENTITY TYPE", entity_type.capitalize()),
    ]

    font_label = _get_font(16, bold=True)
    font_val = _get_font(20)

    # Column 1
    draw.text((60, grid_y), labels[0][0], fill=(100, 116, 139, 255), font=font_label)
    draw.text((60, grid_y + 26), labels[0][1], fill=(241, 245, 249, 255), font=font_val)

    draw.text((60, grid_y + 75), labels[1][0], fill=(100, 116, 139, 255), font=font_label)
    draw.text((60, grid_y + 101), labels[1][1], fill=(56, 189, 248, 255), font=font_val)

    # Column 2
    draw.text((430, grid_y), labels[2][0], fill=(100, 116, 139, 255), font=font_label)
    draw.text((430, grid_y + 26), labels[2][1], fill=(241, 245, 249, 255), font=font_val)

    draw.text((430, grid_y + 75), labels[3][0], fill=(100, 116, 139, 255), font=font_label)
    draw.text((430, grid_y + 101), labels[3][1], fill=(241, 245, 249, 255), font=font_val)

    # 5. Embedded Mini QR Code
    qr_data = f"https://t.me/{username}" if username else f"tg://user?id={entity_id}"
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="white", back_color="#0f172a").convert("RGBA")
    qr_img = qr_img.resize((150, 150), Image.Resampling.NEAREST)

    qr_x, qr_y = WIDTH - 220, 265
    card.paste(qr_img, (qr_x, qr_y))
    draw.text((qr_x + 10, qr_y + 155), "SCAN TO OPEN", fill=(100, 116, 139, 255), font=_get_font(14, bold=True))

    # 6. Footer & Security Watermark
    footer_y = HEIGHT - 65
    draw.line([(50, footer_y - 15), (WIDTH - 50, footer_y - 15)], fill=(30, 41, 59, 255), width=1)
    draw.text((60, footer_y), "AUTHENTICATED TELEGRAM OSINT REPORT", fill=(71, 85, 105, 255), font=_get_font(15))
    draw.text((WIDTH - 360, footer_y), f"SEC-HASH: {abs(hash(str(entity_id) + str(datetime.date.today()))):X}-SENTINEL", fill=(71, 85, 105, 255), font=_get_font(15))

    # Save output
    output_path = EXPORTS_DIR / f"idcard_{entity_id}_{abs(hash(title)) % 10000}.png"
    card.save(str(output_path), "PNG")
    return output_path
