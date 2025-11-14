"""Entrypoint for the Telegram channel management bot."""
from __future__ import annotations

import logging

from pyrogram import Client

from config import API_HASH, API_ID, BOT_TOKEN, LOG_LEVEL
from db import ensure_indexes
from handlers import channel_events, commands

logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_client() -> Client:
    return Client(
        "channel-management-bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True,
    )


def main() -> None:
    logger.info("Starting channel management bot")
    ensure_indexes()
    app = build_client()
    commands.register(app)
    channel_events.register(app)
    app.run()


if __name__ == "__main__":
    main()
