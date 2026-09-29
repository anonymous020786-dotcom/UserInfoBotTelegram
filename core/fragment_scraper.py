import re
import aiohttp
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

from core.osint_analyzer import validate_telegram_username


async def scrape_fragment_username(username: str) -> Dict[str, Any]:
    """
    Scrapes 100% live data directly from Fragment.com (The official TON-Telegram NFT marketplace).
    Extracts status (Taken, Sold, On Auction, Available), current bid/price in TON, and auction details.
    """
    clean_handle = username.strip().lstrip("@")
    val = validate_telegram_username(clean_handle)
    fragment_url = f"https://fragment.com/username/{clean_handle}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    res_data = {
        "username": clean_handle,
        "is_valid_format": val["is_valid_format"],
        "length": val["length"],
        "fragment_url": fragment_url,
        "status": "Available / Unlisted",
        "price_ton": None,
        "price_usd_est": None,
        "highest_bid": None,
        "owner_address": None,
        "auction_ends": None,
        "is_auction_active": False,
        "source": "Fragment.com Direct"
    }

    if not val["is_valid_format"] and not (clean_handle.isdigit() and len(clean_handle) == 7):
        res_data["status"] = "Invalid Telegram Format"
        return res_data

    try:
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(fragment_url, headers=headers) as resp:
                if resp.status == 404:
                    res_data["status"] = "Not Found / Unregistered"
                    return res_data
                elif resp.status != 200:
                    res_data["status"] = f"HTTP {resp.status}"
                    return res_data

                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # Status element: <span class="tm-section-header-status ...">Taken / Sold / On Auction / Available</span>
        status_el = soup.find("span", class_="tm-section-header-status")
        if status_el:
            res_data["status"] = status_el.text.strip()
        else:
            # Check table or alternative tags
            avail_tag = soup.find("div", class_="tm-status-avail")
            if avail_tag:
                res_data["status"] = avail_tag.text.strip()

        # Price / Valuation in TON: <div class="tm-value icon-before icon-ton">...</div>
        price_el = soup.find("div", class_="tm-value")
        if price_el:
            raw_price = price_el.text.strip()
            # Clean string
            clean_price = re.sub(r'[^\d,.]', '', raw_price).replace(',', '')
            try:
                numeric_ton = float(clean_price)
                res_data["price_ton"] = numeric_ton
                res_data["price_usd_est"] = round(numeric_ton * 5.80, 2)
            except Exception:
                res_data["price_ton_raw"] = raw_price

        # Highest Bid or Min Bid
        bid_el = soup.find("span", class_="tm-value-bid")
        if bid_el:
            res_data["highest_bid"] = bid_el.text.strip()

        # Check auction countdown
        countdown_el = soup.find("div", class_="tm-countdown-timer")
        if countdown_el:
            res_data["auction_ends"] = countdown_el.text.strip()
            res_data["is_auction_active"] = True

        # Owner TON Wallet / NFT contract if displayed
        wallet_el = soup.find("a", class_="tm-wallet")
        if wallet_el:
            res_data["owner_address"] = wallet_el.text.strip()

        return res_data
    except Exception as e:
        res_data["status"] = f"Lookup Error ({type(e).__name__})"
        return res_data


async def scrape_fragment_phone_number(raw_phone: str) -> Dict[str, Any]:
    """
    Scrapes live Fragment.com NFT data for Telegram Anonymous Virtual Numbers (+888 XXXX XXXX).
    Extracts status (Taken, Sold, On Auction, Available), valuation in TON, and NFT link.
    """
    clean_digits = re.sub(r'[^\d]', '', raw_phone.strip())
    fragment_url = f"https://fragment.com/number/{clean_digits}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    res_data = {
        "raw_phone": raw_phone,
        "digits": clean_digits,
        "fragment_url": fragment_url,
        "is_fragment_888": clean_digits.startswith("888"),
        "status": "Available / Unlisted",
        "price_ton": None,
        "price_usd_est": None,
        "highest_bid": None,
        "owner_address": None,
        "auction_ends": None,
        "source": "Fragment.com Direct"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(fragment_url, headers=headers) as resp:
                if resp.status == 404:
                    res_data["status"] = "Not Found / Unregistered"
                    return res_data
                elif resp.status != 200:
                    res_data["status"] = f"HTTP {resp.status}"
                    return res_data

                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # Status
        status_el = soup.find("span", class_="tm-section-header-status")
        if status_el:
            res_data["status"] = status_el.text.strip()
        else:
            avail_tag = soup.find("div", class_="tm-status-avail")
            if avail_tag:
                res_data["status"] = avail_tag.text.strip()

        # Valuation in TON
        price_el = soup.find("div", class_="tm-value")
        if price_el:
            raw_price = price_el.text.strip()
            clean_price = re.sub(r'[^\d,.]', '', raw_price).replace(',', '')
            try:
                numeric_ton = float(clean_price)
                res_data["price_ton"] = numeric_ton
                res_data["price_usd_est"] = round(numeric_ton * 5.80, 2)
            except Exception:
                res_data["price_ton_raw"] = raw_price

        # Highest Bid
        bid_el = soup.find("span", class_="tm-value-bid")
        if bid_el:
            res_data["highest_bid"] = bid_el.text.strip()

        # Auction Timer
        countdown_el = soup.find("div", class_="tm-countdown-timer")
        if countdown_el:
            res_data["auction_ends"] = countdown_el.text.strip()

        # Owner TON Wallet
        wallet_el = soup.find("a", class_="tm-wallet")
        if wallet_el:
            res_data["owner_address"] = wallet_el.text.strip()

        return res_data
    except Exception as e:
        res_data["status"] = f"Lookup Error ({type(e).__name__})"
        return res_data

