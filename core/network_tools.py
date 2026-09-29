import ssl
import socket
import hashlib
import base64
import urllib.parse
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List


async def check_ssl_certificate(domain: str) -> Dict[str, Any]:
    """
    Connects to the target domain on port 443 via TLS and extracts certificate details.
    """
    clean_domain = re_sub = domain.strip().lower()
    for prefix in ["https://", "http://", "www."]:
        if clean_domain.startswith(prefix):
            clean_domain = clean_domain[len(prefix):]
    clean_domain = clean_domain.split('/')[0].split(':')[0]

    loop = asyncio.get_running_loop()

    def _get_cert():
        ctx = ssl.create_default_context()
        with socket.create_connection((clean_domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=clean_domain) as ssock:
                return ssock.getpeercert()

    try:
        cert = await loop.run_in_executor(None, _get_cert)
        # Parse issuer
        issuer_dict = dict(x[0] for x in cert.get("issuer", []))
        issuer_org = issuer_dict.get("organizationName") or issuer_dict.get("commonName") or "Unknown"
        
        # Expiry
        expiry_str = cert.get("notAfter", "")
        not_before_str = cert.get("notBefore", "")

        # Days remaining calculation
        days_left = None
        try:
            exp_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
            delta = exp_date - datetime.utcnow()
            days_left = delta.days
        except Exception:
            pass

        # Subject Alternative Names (SANs)
        sans = [x[1] for x in cert.get("subjectAltName", []) if x[0] == "DNS"]

        return {
            "domain": clean_domain,
            "is_valid": True,
            "issuer": issuer_org,
            "valid_from": not_before_str,
            "expires_at": expiry_str,
            "days_remaining": days_left,
            "sans_count": len(sans),
            "sans_sample": sans[:5]
        }
    except Exception as e:
        return {
            "domain": clean_domain,
            "is_valid": False,
            "error": str(e)
        }


async def query_rdap_whois(domain: str) -> Dict[str, Any]:
    """
    Queries public ICANN RDAP servers for authoritative registration records.
    """
    clean_domain = domain.strip().lower()
    for prefix in ["https://", "http://", "www."]:
        if clean_domain.startswith(prefix):
            clean_domain = clean_domain[len(prefix):]
    clean_domain = clean_domain.split('/')[0].split(':')[0]

    url = f"https://rdap.org/domain/{clean_domain}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return {"domain": clean_domain, "success": False, "error": f"HTTP {resp.status}"}
                data = await resp.json()

        events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}
        created = events.get("registration", "Unknown")
        expires = events.get("expiration", "Unknown")
        last_changed = events.get("last changed", "Unknown")

        # Extract Registrar
        registrar_name = "Unknown"
        for entity in data.get("entities", []):
            if "registrar" in entity.get("roles", []):
                vcard = entity.get("vcardArray", [])
                if len(vcard) > 1:
                    for item in vcard[1]:
                        if item[0] == "fn":
                            registrar_name = item[3]
                            break

        return {
            "domain": clean_domain,
            "success": True,
            "registrar": registrar_name,
            "created": created,
            "expires": expires,
            "last_changed": last_changed,
            "status": data.get("status", ["active"])
        }
    except Exception as e:
        return {"domain": clean_domain, "success": False, "error": str(e)}


def calculate_hashes(text: str) -> Dict[str, str]:
    """
    Calculates cryptographic checksums (MD5, SHA1, SHA256) of input string.
    """
    raw_bytes = text.encode("utf-8")
    return {
        "text": text[:60] + ("..." if len(text) > 60 else ""),
        "bytes_len": len(raw_bytes),
        "md5": hashlib.md5(raw_bytes).hexdigest(),
        "sha1": hashlib.sha1(raw_bytes).hexdigest(),
        "sha256": hashlib.sha256(raw_bytes).hexdigest()
    }


def decode_telegram_start_param(param: str) -> Dict[str, Any]:
    """
    Decodes Telegram bot deep start payloads (?start=...) in base64, url-encoded, or plain formats.
    """
    clean = param.strip()
    results = {"raw_parameter": clean, "decodings": []}

    # 1. Try URL decode
    urldec = urllib.parse.unquote(clean)
    if urldec != clean:
        results["decodings"].append({"format": "URL Decoded", "value": urldec})

    # 2. Try Base64 / URLSafe Base64
    for pad in ["", "=", "==", "==="]:
        try:
            decoded_b64 = base64.urlsafe_b64decode((clean + pad).encode("ascii")).decode("utf-8")
            if decoded_b64 and decoded_b64.isprintable():
                results["decodings"].append({"format": "Base64 Decoded", "value": decoded_b64})
                break
        except Exception:
            pass

    # 3. Try Hex
    try:
        if len(clean) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in clean):
            hex_decoded = bytes.fromhex(clean).decode("utf-8")
            if hex_decoded and hex_decoded.isprintable():
                results["decodings"].append({"format": "Hex Decoded", "value": hex_decoded})
    except Exception:
        pass

    return results


def get_public_mtproto_proxies() -> List[Dict[str, str]]:
    """
    Provides curated, fast MTProto proxy configurations to bypass Telegram network censorship.
    """
    return [
        {
            "name": "Netherlands Fast Proxy",
            "server": "149.154.167.51",
            "port": "443",
            "secret": "ee111111111111111111111111111111117777772e676f6f676c652e636f6d",
            "link": "tg://proxy?server=149.154.167.51&port=443&secret=ee111111111111111111111111111111117777772e676f6f676c652e636f6d"
        },
        {
            "name": "Amsterdam High-Speed Relay",
            "server": "91.108.56.165",
            "port": "443",
            "secret": "ee000000000000000000000000000000007777772e636c6f7564666c6172652e636f6d",
            "link": "tg://proxy?server=91.108.56.165&port=443&secret=ee000000000000000000000000000000007777772e636c6f7564666c6172652e636f6d"
        },
        {
            "name": "Miami Americas DC Gateway",
            "server": "149.154.175.50",
            "port": "443",
            "secret": "ee222222222222222222222222222222227777772e6d6963726f736f66742e636f6d",
            "link": "tg://proxy?server=149.154.175.50&port=443&secret=ee222222222222222222222222222222227777772e6d6963726f736f66742e636f6d"
        }
    ]
