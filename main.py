from __future__ import annotations

from bot import APP
from bot.config import logger


def main() -> None:
    logger.info("Starting Auto Forward Bot")
    APP.run()


if __name__ == "__main__":
    main()
