"""
BEN Discord Bot - Configuration Module
Created with a professional transparent dark-aesthetic UI.
"""
import os
from dotenv import load_dotenv
load_dotenv()
# Bot Credentials & Settings
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
APPLICATION_ID = os.getenv("APPLICATION_ID", None)
# Bot Identity
BOT_NAME = "BEN"
BOT_VERSION = "2.5.0"
BOT_DESCRIPTION = "The all-in-one professional Discord management, community, and entertainment powerhouse."
BOT_FOOTER = f"{BOT_NAME} System • High Performance"
# Visual Aesthetics - Transparent / Dark Mode Colors
# 0x2B2D31 is Discord's native dark-theme background color.
# Using this color produces the acclaimed 'transparent / seamless embed' effect.
COLOR_TRANSPARENT = 0x2B2D31
COLOR_DEFAULT = 0x2B2D31
COLOR_PRIMARY = 0x5865F2      # Discord Blurple
COLOR_SUCCESS = 0x57F287      # Mint Green
COLOR_ERROR = 0xED4245        # Crimson Red
COLOR_WARNING = 0xFEE75C      # Golden Yellow
COLOR_INFO = 0x3498DB         # Ice Blue
COLOR_ACCENT = 0x9B59B6       # Amethyst Purple
# Custom UI Emojis & Symbols (Clean & Professional)
EMOJIS = {
    # System & Status
    "dot": "•",
    "arrow": "›",
    "bullet": "◈",
    "diamond": "◆",
    "check": "✅",
    "cross": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳",
    "sparkles": "✨",
    "shield": "🛡️",
    "gear": "⚙️",
