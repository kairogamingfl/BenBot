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
