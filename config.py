"""Configuration utilities for the channel management bot."""
from __future__ import annotations

import os
from typing import Final

BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "")
API_ID: Final[int] = int(os.getenv("API_ID", "0") or 0)
API_HASH: Final[str] = os.getenv("API_HASH", "")
MONGO_URI: Final[str] = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME: Final[str] = os.getenv("MONGO_DB_NAME", "channel_management_bot")
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required. Set it via environment variable.")

if not API_ID or not API_HASH:
    raise RuntimeError("API_ID and API_HASH are required for Pyrogram bots.")
