import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
AVATARS_DIR = DATA_DIR / "avatars"

# Ensure essential directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = [
    int(x.strip()) 
    for x in os.getenv("ADMIN_IDS", "").split(",") 
    if x.strip().isdigit()
]

# Optional MTProto (Telethon) client credentials for deep discovery
API_ID_STR = os.getenv("API_ID", "").strip()
API_HASH = os.getenv("API_HASH", "").strip()
API_ID = int(API_ID_STR) if API_ID_STR.isdigit() else None
SESSION_STRING = os.getenv("SESSION_STRING", "").strip()

# Database Path
DB_PATH = DATA_DIR / "bot_database.sqlite3"

# Rate Limiting (seconds between requests per user)
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

# Bot Metadata
BOT_NAME = "Sentinel OSINT & Finder Bot"
BOT_VERSION = "2.5.0"
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/Telegram")
PROJECT_REPO = "https://github.com/Sentinel-Telegram/UserInfoFinderBot"

# Supported Themes & Languages
SUPPORTED_THEMES = ["cyberpunk", "minimalist", "osint"]
DEFAULT_THEME = "cyberpunk"

SUPPORTED_LANGUAGES = ["en", "es", "hi", "ru", "ar"]
DEFAULT_LANGUAGE = "en"
