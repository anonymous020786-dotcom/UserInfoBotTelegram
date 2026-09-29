from pathlib import Path
from typing import Optional
from config import EXPORTS_DIR


def generate_vcard(
    user_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    bio: Optional[str] = None
) -> Path:
    """
    Generates a standard vCard 3.0 (.vcf) file for a Telegram user.
    """
    clean_fn = first_name or "Telegram"
    clean_ln = last_name or "User"
    full_name = f"{clean_fn} {clean_ln}".strip()
    
    vcard_lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{full_name}",
        f"N:{clean_ln};{clean_fn};;;",
    ]

    if username:
        vcard_lines.append(f"X-TELEGRAM-USERNAME:@{username}")
        vcard_lines.append(f"URL:https://t.me/{username}")

    vcard_lines.append(f"X-TELEGRAM-ID:{user_id}")
    vcard_lines.append(f"NOTE:Telegram ID: {user_id}\\nUsername: @{username or 'None'}\\nBio: {bio or 'N/A'}")
    vcard_lines.append("END:VCARD")

    vcard_content = "\r\n".join(vcard_lines)
    output_path = EXPORTS_DIR / f"contact_{user_id}.vcf"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(vcard_content)

    return output_path
