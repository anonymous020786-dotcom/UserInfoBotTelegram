import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DB_PATH, DEFAULT_LANGUAGE, DEFAULT_THEME


async def init_db():
    """Initializes SQLite database tables and indexes."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                theme TEXT DEFAULT 'cyberpunk',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                query_count INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_id INTEGER,
                target_username TEXT,
                target_type TEXT,
                target_title TEXT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_id INTEGER,
                target_username TEXT,
                target_title TEXT,
                target_type TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, target_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_by INTEGER NOT NULL,
                category TEXT NOT NULL,
                username_or_link TEXT NOT NULL,
                title TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS identity_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_stats (
                metric_key TEXT PRIMARY KEY,
                metric_value INTEGER DEFAULT 0
            )
        """)

        # Indexes for fast querying
        await db.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON search_history(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_identity_target ON identity_history(target_id)")

        await db.commit()


async def get_or_create_user(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str]) -> Dict[str, Any]:
    """Retrieves user profile or inserts a new record."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await db.execute("""
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, last_active = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (username, first_name, last_name, user_id))
                await db.commit()
                return dict(row)

        # Create new user
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, language, theme)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, DEFAULT_LANGUAGE, DEFAULT_THEME))
        await db.commit()

        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            new_row = await cursor.fetchone()
            return dict(new_row) if new_row else {}


async def update_user_preference(user_id: int, language: Optional[str] = None, theme: Optional[str] = None):
    """Updates user language or theme setting."""
    async with aiosqlite.connect(DB_PATH) as db:
        if language:
            await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
        if theme:
            await db.execute("UPDATE users SET theme = ? WHERE user_id = ?", (theme, user_id))
        await db.commit()


async def increment_user_query(user_id: int):
    """Increments user's total query count and bot overall queries."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET query_count = query_count + 1 WHERE user_id = ?", (user_id,))
        await db.execute("""
            INSERT INTO bot_stats (metric_key, metric_value) 
            VALUES ('total_queries', 1) 
            ON CONFLICT(metric_key) DO UPDATE SET metric_value = metric_value + 1
        """)
        await db.commit()


async def record_search(user_id: int, target_id: Optional[int], target_username: Optional[str], target_type: str, target_title: str):
    """Logs a search into history and keeps only top 30 per user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO search_history (user_id, target_id, target_username, target_type, target_title)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, target_id, target_username, target_type, target_title))
        
        # Prune old records beyond 30
        await db.execute("""
            DELETE FROM search_history 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM search_history WHERE user_id = ? ORDER BY id DESC LIMIT 30
            )
        """, (user_id, user_id))
        await db.commit()


async def get_user_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetches user search history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM search_history 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def clear_user_history(user_id: int):
    """Clears search history for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
        await db.commit()


async def add_favorite(user_id: int, target_id: int, target_username: Optional[str], target_title: str, target_type: str) -> bool:
    """Adds an item to personal favorites."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO favorites (user_id, target_id, target_username, target_title, target_type)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, target_id, target_username, target_title, target_type))
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_favorite(user_id: int, target_id: int) -> bool:
    """Removes an item from favorites."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM favorites WHERE user_id = ? AND target_id = ?", (user_id, target_id))
        await db.commit()
        return cur.rowcount > 0


async def is_favorite(user_id: int, target_id: int) -> bool:
    """Checks if an item is already bookmarked."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM favorites WHERE user_id = ? AND target_id = ?", (user_id, target_id)) as cursor:
            return (await cursor.fetchone()) is not None


async def get_favorites(user_id: int) -> List[Dict[str, Any]]:
    """Gets all bookmarked entities for user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM favorites WHERE user_id = ? ORDER BY id DESC", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def log_identity(target_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
    """Logs name/username to identify past alias changes."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT username, first_name, last_name FROM identity_history 
            WHERE target_id = ? ORDER BY id DESC LIMIT 1
        """, (target_id,)) as cursor:
            last = await cursor.fetchone()
            if last and last["username"] == username and last["first_name"] == first_name and last["last_name"] == last_name:
                return  # No change

        await db.execute("""
            INSERT INTO identity_history (target_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (target_id, username, first_name, last_name))
        await db.commit()


async def get_identity_history(target_id: int) -> List[Dict[str, Any]]:
    """Fetches tracked past usernames and names for an entity."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT username, first_name, last_name, seen_at 
            FROM identity_history 
            WHERE target_id = ? 
            ORDER BY id DESC LIMIT 10
        """, (target_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def submit_community(submitted_by: int, category: str, link: str, title: str, description: str) -> int:
    """Submits a new channel/group for review."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO submissions (submitted_by, category, username_or_link, title, description)
            VALUES (?, ?, ?, ?, ?)
        """, (submitted_by, category, link, title, description))
        await db.commit()
        return cursor.lastrowid


async def get_pending_submissions() -> List[Dict[str, Any]]:
    """Retrieves pending community submissions for admin review."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM submissions WHERE status = 'pending' ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_submission_status(sub_id: int, status: str):
    """Updates submission status (approved or rejected)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE submissions SET status = ? WHERE id = ?", (status, sub_id))
        await db.commit()


async def get_bot_stats() -> Dict[str, Any]:
    """Aggregates all bot statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM search_history") as cur:
            total_searches = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM favorites") as cur:
            total_favorites = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM submissions WHERE status = 'approved'") as cur:
            approved_submissions = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM submissions WHERE status = 'pending'") as cur:
            pending_submissions = (await cur.fetchone())[0]

        return {
            "total_users": total_users,
            "total_searches": total_searches,
            "total_favorites": total_favorites,
            "approved_submissions": approved_submissions,
            "pending_submissions": pending_submissions
        }
