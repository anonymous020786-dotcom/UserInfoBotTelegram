import math
import re
from typing import Dict, Any, Optional

from core.reg_date_estimator import estimate_registration_date

INT32_MAX = 2_147_483_647


def analyze_telegram_id(raw_id_input: int | str) -> Dict[str, Any]:
    """
    Performs forensic 64-bit ID mathematics, architectural bit-length analysis,
    peer type classification, and channel offset resolution.
    """
    try:
        numeric_id = int(str(raw_id_input).strip())
    except ValueError:
        return {"error": "Invalid numeric ID format"}

    abs_id = abs(numeric_id)
    bit_length = abs_id.bit_length()
    hex_repr = hex(abs_id).upper()
    bin_repr = bin(abs_id)

    # Architectural Classification
    if numeric_id > 0:
        peer_type = "Private User / Bot Entity"
        underlying_channel_id = None
        is_channel_supergroup = False
    elif numeric_id < -1_000_000_000_000:
        peer_type = "Supergroup / Broadcast Channel"
        underlying_channel_id = abs_id - 1_000_000_000_000
        is_channel_supergroup = True
    elif numeric_id < 0:
        peer_type = "Legacy Basic Group (Small Group)"
        underlying_channel_id = None
        is_channel_supergroup = False
    else:
        peer_type = "System Root / Zero"
        underlying_channel_id = None
        is_channel_supergroup = False

    # 32-bit vs 64-bit Epoch
    is_64bit = abs_id > INT32_MAX
    epoch_architecture = (
        "Modern 64-bit Epoch (Post-2021 Expansion)" if is_64bit else "Legacy 32-bit Epoch (2013-2021 Genesis)"
    )

    # Sequential milestone & regression
    target_id_for_age = underlying_channel_id if is_channel_supergroup else abs_id
    age_est = estimate_registration_date(target_id_for_age)

    return {
        "raw_id": numeric_id,
        "abs_id": abs_id,
        "peer_type": peer_type,
        "is_channel_supergroup": is_channel_supergroup,
        "underlying_channel_id": underlying_channel_id,
        "bit_length": bit_length,
        "hex_representation": hex_repr,
        "binary_representation": bin_repr,
        "is_64bit": is_64bit,
        "architecture": epoch_architecture,
        "estimated_registration": age_est["estimated_month"],
        "relative_age": age_est["relative_age"],
        "confidence": age_est["confidence"]
    }


def analyze_bot_token_forensics(token: str) -> Dict[str, Any]:
    """
    Decodes bot token structure, extracts embedded bot ID without network call,
    estimates bot age from ID, and verifies token structure.
    """
    token_clean = token.strip()
    match = re.match(r'^(\d{6,15}):([a-zA-Z0-9_-]{30,50})$', token_clean)

    if not match:
        return {
            "is_valid_format": False,
            "error": "Token does not match Telegram Bot API format <bot_id>:<secret>"
        }

    bot_id = int(match.group(1))
    secret = match.group(2)

    id_analysis = analyze_telegram_id(bot_id)

    return {
        "is_valid_format": True,
        "bot_id": bot_id,
        "secret_prefix": f"{secret[:6]}...{secret[-4:]}",
        "secret_length": len(secret),
        "id_forensics": id_analysis
    }
