from __future__ import annotations

from .config import APP

# Import handlers so that Pyrogram registers them when APP is used.
from . import handlers  # noqa: F401

__all__ = ["APP"]
