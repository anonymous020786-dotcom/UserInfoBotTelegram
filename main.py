import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import BOT_TOKEN, RATE_LIMIT_DELAY, BOT_NAME, BOT_VERSION, API_ID, API_HASH
from database import init_db
from core.telethon_engine import get_telethon_client
from middlewares.throttling import ThrottlingMiddleware
from middlewares.tracking import UserTrackingMiddleware

# Import Handlers
from handlers import (
    start,
    user_info,
    forward_inspector,
    channel_finder,
    group_finder,
    directory,
    tools,
    export,
    favorites,
    history,
    submission,
    settings,
    admin,
    inline_mode
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sentinel")


async def setup_bot_commands(bot: Bot):
    """Registers official bot commands menu in Telegram UI."""
    commands = [
        BotCommand(command="start", description="🚀 Launch Main OSINT Dashboard"),
        BotCommand(command="id", description="🆔 View Your Own Profile Card & ID"),
        BotCommand(command="channel", description="📢 Search & Discover Channels"),
        BotCommand(command="group", description="👥 Search & Discover Groups"),
        BotCommand(command="directory", description="📂 Curated 12-Topic Directory"),
        BotCommand(command="tools", description="🛠️ OSINT & Developer Utilities"),
        BotCommand(command="favorites", description="⭐ Access Bookmarked Entities"),
        BotCommand(command="history", description="🕒 View Past Lookup History"),
        BotCommand(command="settings", description="⚙️ Language & Visual Themes"),
        BotCommand(command="features", description="📋 47+ Features Breakdown"),
        BotCommand(command="help", description="📖 User Manual & Guide"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info("Bot commands menu registered successfully.")
    except Exception as e:
        logger.warning(f"Could not register bot commands menu: {e}")


async def main():
    """Application entrypoint."""
    banner = r"""
    ========================================================
       _____ ______ _   _ _______ _____ _   _ ______ _      
      / ____|  ____| \ | |__   __|_   _| \ | |  ____| |     
     | (___ | |__  |  \| |  | |    | | |  \| | |__  | |     
      \___ \|  __| | . ` |  | |    | | | . ` |  __| | |     
      ____) | |____| |\  |  | |   _| |_| |\  | |____| |____ 
     |_____/|______|_| \_|  |_|  |_____|_| \_|______|______|
                                                            
      Sentinel OSINT & Finder Bot v2.5.0
      Advanced OSINT, Intelligence & Community Discovery Engine
    ========================================================
    """
    print(banner)

    # 1. Initialize SQLite Database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully.")

    # 2. Check Bot Token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error(
            "CRITICAL: BOT_TOKEN is missing! Please configure BOT_TOKEN in your .env file."
        )
        logger.info("A template has been generated in .env.example.")
        return

    # 3. Initialize MTProto client if configured
    if API_ID and API_HASH:
        logger.info("Connecting MTProto Telethon engine...")
        asyncio.create_task(get_telethon_client())
    else:
        logger.info("MTProto credentials not configured; operating in Bot API + Web Direct mode.")

    # 4. Initialize Bot & Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 5. Attach Middlewares
    dp.message.middleware(ThrottlingMiddleware(delay=RATE_LIMIT_DELAY))
    dp.callback_query.middleware(ThrottlingMiddleware(delay=RATE_LIMIT_DELAY))
    dp.message.middleware(UserTrackingMiddleware())
    dp.callback_query.middleware(UserTrackingMiddleware())

    # 6. Register Routers (order matters for matching precedence)
    dp.include_router(start.router)
    dp.include_router(forward_inspector.router)
    dp.include_router(channel_finder.router)
    dp.include_router(group_finder.router)
    dp.include_router(directory.router)
    dp.include_router(tools.router)
    dp.include_router(export.router)
    dp.include_router(favorites.router)
    dp.include_router(history.router)
    dp.include_router(submission.router)
    dp.include_router(settings.router)
    dp.include_router(admin.router)
    dp.include_router(inline_mode.router)
    dp.include_router(user_info.router)  # User lookup catch-all at the end

    # 7. Register Commands Menu
    await setup_bot_commands(bot)

    # 8. Start Polling
    try:
        bot_user = await bot.get_me()
        logger.info(f"Bot connected: @{bot_user.username} (ID: {bot_user.id})")
        logger.info("Polling for updates started...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Fatal error while polling: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot shutdown cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application stopped by operator.")
