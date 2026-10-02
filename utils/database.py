"""
BEN Discord Bot - Async SQLite Database Layer
Handles persistent storage for Guild Configurations, Tickets, Applications, Reaction Roles, and Logs.
"""
import os
import aiosqlite
from typing import Optional, Dict, Any, List
import config

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        # Ensure data folder exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def initialize(self):
        """Initializes database schema and tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    welcome_channel_id INTEGER,
                    welcome_message TEXT,
                    welcome_enabled INTEGER DEFAULT 1,
                    leave_channel_id INTEGER,
                    leave_message TEXT,
                    leave_enabled INTEGER DEFAULT 1,
                    log_channel_id INTEGER,
                    log_enabled INTEGER DEFAULT 1,
                    ticket_category_id INTEGER,
                    ticket_log_channel_id INTEGER,
                    ticket_support_role_id INTEGER,
                    ticket_counter INTEGER DEFAULT 0,
                    app_channel_id INTEGER,
                    app_review_channel_id INTEGER,
                    app_role_id INTEGER
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    ticket_num INTEGER NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    closed_by INTEGER
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    app_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    answers_json TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    reviewer_id INTEGER,
                    review_note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    emoji TEXT,
                    label TEXT,
                    style TEXT DEFAULT 'secondary'
                )
            """)
            await db.commit()

    # --- Guild Settings ---
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                # Insert default record if not found
                await db.execute(
                    "INSERT INTO guild_settings (guild_id) VALUES (?)", (guild_id,)
                )
                await db.commit()
                return {"guild_id": guild_id}

    async def update_guild_setting(self, guild_id: int, key: str, value: Any):
        # Whitelist keys to prevent arbitrary SQL injection
        allowed_keys = {
            "welcome_channel_id", "welcome_message", "welcome_enabled",
            "leave_channel_id", "leave_message", "leave_enabled",
            "log_channel_id", "log_enabled",
            "ticket_category_id", "ticket_log_channel_id", "ticket_support_role_id", "ticket_counter",
            "app_channel_id", "app_review_channel_id", "app_role_id"
        }
        if key not in allowed_keys:
            raise ValueError(f"Invalid guild setting key: {key}")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"""
                INSERT INTO guild_settings (guild_id, {key}) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET {key} = excluded.{key}
                """,
                (guild_id, value)
            )
            await db.commit()

    # --- Tickets ---
    async def increment_ticket_counter(self, guild_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO guild_settings (guild_id, ticket_counter)
                VALUES (?, 1)
                ON CONFLICT(guild_id) DO UPDATE SET ticket_counter = ticket_counter + 1
                """,
                (guild_id,)
            )
            await db.commit()
            async with db.execute(
                "SELECT ticket_counter FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 1

    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int, ticket_num: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO tickets (guild_id, channel_id, user_id, ticket_num, status)
                VALUES (?, ?, ?, ?, 'open')
                """,
                (guild_id, channel_id, user_id, ticket_num)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM tickets WHERE channel_id = ? AND status = 'open'", (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def close_ticket(self, channel_id: int, closed_by: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE tickets
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP, closed_by = ?
                WHERE channel_id = ? AND status = 'open'
                """,
                (closed_by, channel_id)
            )
            await db.commit()

    # --- Applications ---
    async def create_application(self, guild_id: int, user_id: int, answers_json: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO applications (guild_id, user_id, answers_json, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (guild_id, user_id, answers_json)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM applications WHERE app_id = ?", (app_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_application_status(self, app_id: int, status: str, reviewer_id: int, note: Optional[str] = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE applications
                SET status = ?, reviewer_id = ?, review_note = ?
                WHERE app_id = ?
                """,
                (status, reviewer_id, note, app_id)
            )
            await db.commit()

    # --- Reaction Roles ---
    async def add_reaction_role(self, guild_id: int, channel_id: int, message_id: int, role_id: int, emoji: str, label: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO reaction_roles (guild_id, channel_id, message_id, role_id, emoji, label)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (guild_id, channel_id, message_id, role_id, emoji, label)
            )
            await db.commit()

    async def get_reaction_roles_for_message(self, message_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM reaction_roles WHERE message_id = ?", (message_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
