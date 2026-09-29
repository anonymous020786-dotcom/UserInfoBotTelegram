import base64
import struct
from typing import Optional, Dict, Any


DC_DATA: Dict[int, Dict[str, str]] = {
    1: {
        "name": "Pluto (DC1)",
        "location": "Miami, Florida, USA",
        "ip": "149.154.175.50",
        "region": "Americas",
        "flag": "🇺🇸"
    },
    2: {
        "name": "Venus (DC2)",
        "location": "Amsterdam, Netherlands",
        "ip": "149.154.167.51",
        "region": "Europe / Middle East / Africa",
        "flag": "🇳🇱"
    },
    3: {
        "name": "Aurora (DC3)",
        "location": "Miami, Florida, USA",
        "ip": "149.154.175.100",
        "region": "Americas Backup / Redundancy",
        "flag": "🇺🇸"
    },
    4: {
        "name": "Vesta (DC4)",
        "location": "Amsterdam, Netherlands",
        "ip": "149.154.167.91",
        "region": "Europe / Central Asia",
        "flag": "🇳🇱"
    },
    5: {
        "name": "Flora (DC5)",
        "location": "Singapore",
        "ip": "91.108.56.130",
        "region": "Asia & Oceania",
        "flag": "🇸🇬"
    }
}


def decode_file_id_dc(file_id: str) -> Optional[int]:
    """
    Decodes the Telegram Data Center (DC) ID from a Telegram Bot API file_id.
    Telegram encodes the DC ID into the 4th/5th byte of the base64-decoded file_id.
    """
    if not file_id:
        return None
    try:
        # Standardize padding for base64
        padded = file_id + "=" * (-len(file_id) % 4)
        padded = padded.replace("-", "+").replace("_", "/")
        raw = base64.b64decode(padded)
        if len(raw) >= 8:
            # Type is in the first byte or unpacked struct
            # In Telegram Bot API v4+, DC ID is stored at byte offset 4 or unpacked as uint32
            dc_id = raw[4]
            if 1 <= dc_id <= 5:
                return dc_id
            
            # Alternative unpack: int at offset 0 or 4
            unpacked = struct.unpack("<i", raw[:4])[0]
            candidate_dc = (unpacked >> 16) & 0x7
            if 1 <= candidate_dc <= 5:
                return candidate_dc
    except Exception:
        pass
    return None


def get_dc_info(dc_id: Optional[int]) -> Dict[str, Any]:
    """Returns comprehensive info about a Telegram Data Center."""
    if dc_id and dc_id in DC_DATA:
        return {
            "dc_id": dc_id,
            **DC_DATA[dc_id],
            "status": "Identified"
        }
    return {
        "dc_id": dc_id or "Unknown",
        "name": "Unknown DC",
        "location": "Global Telegram Cloud",
        "ip": "N/A",
        "region": "Undetermined (Private / Hidden)",
        "flag": "🌐",
        "status": "Unresolved"
    }
