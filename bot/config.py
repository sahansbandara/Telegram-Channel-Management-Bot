from __future__ import annotations

import logging
import os
from pathlib import Path

from pyrogram import Client

from config_store import ConfigStore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_ID = int(os.environ.get("API_ID", "25838967"))
API_HASH = os.environ.get("API_HASH", "bca41bb451ef89ff1ae3129581ce78e5")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8126372548:AAGzeKrSmrjEaDLiTPBMxkYMALU7kYF3Yc4")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError(
        "API_ID, API_HASH, and BOT_TOKEN environment variables must be provided."
    )


APP = Client(
    "auto_forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

CONFIG_PATH = Path("data/config.json")
STORE = ConfigStore(CONFIG_PATH)
STORE.load()
