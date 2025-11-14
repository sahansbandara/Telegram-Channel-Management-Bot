from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Tuple

from pyrogram.enums import ChatType


ForwardKey = Tuple[int, int, int]


@dataclass(frozen=True)
class ChatAccessInfo:
    chat_id: int
    display_name: str
    is_public: bool
    chat_type: ChatType


FORWARD_HISTORY: Dict[ForwardKey, Deque[Tuple[int, int]]] = defaultdict(deque)
DEDUPLICATION_HISTORY_LIMIT = 1000
DEDUPLICATION_CACHE: Dict[int, Deque[str]] = defaultdict(deque)
PENDING_ACTIONS: Dict[int, Dict[str, object]] = {}
