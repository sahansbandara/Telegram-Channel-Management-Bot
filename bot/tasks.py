from __future__ import annotations

import html
import re
from typing import Optional, Tuple

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import Message

from config_store import (
    DEFAULT_MAX_MEDIA_SIZE,
    DEFAULT_MAX_MEDIA_SIZE_MB,
    ForwardTask,
)

from .config import logger
from .state import (
    DEDUPLICATION_CACHE,
    DEDUPLICATION_HISTORY_LIMIT,
    FORWARD_HISTORY,
    ForwardKey,
)
from .ui import describe_selected_media
from .text import MEDIA_FILTER_OPTIONS, TASK_CARD

BYTES_IN_MB = 1024 * 1024

URL_PATTERN = re.compile(
    r"(?xi)"
    r"(\b(?:https?://|www\.)\S+|\b(?:t\.me|telegram\.me|telegram\.dog)/\S+)"
)


def resolve_history_key(task: ForwardTask) -> ForwardKey:
    return (task.task_id, task.source_id, task.target_id)


def register_forwarded_message(task: ForwardTask, original: Message, forwarded: Message) -> None:
    key = resolve_history_key(task)
    history = FORWARD_HISTORY[key]
    history.append((original.id, forwarded.id))
    if len(history) > 5000:
        history.popleft()


def dedupe_signature(message: Message) -> Optional[str]:
    if message.text and not message.media:
        text = message.text.strip()
        if text:
            return f"text:{text}"
        return None

    media = (
        message.photo
        or message.video
        or message.document
        or message.animation
        or message.audio
        or message.voice
        or message.video_note
        or message.sticker
    )
    if media:
        unique_id = getattr(media, "file_unique_id", None)
        if unique_id:
            return f"media:{unique_id}"
    return None


def has_seen_duplicate(task_id: int, signature: str) -> bool:
    history = DEDUPLICATION_CACHE[task_id]
    return signature in history


def remember_duplicate_signature(task_id: int, signature: str) -> None:
    history = DEDUPLICATION_CACHE[task_id]
    history.append(signature)
    while len(history) > DEDUPLICATION_HISTORY_LIMIT:
        history.popleft()


def clear_duplicate_history(task_id: int) -> None:
    DEDUPLICATION_CACHE.pop(task_id, None)


def find_forwarded_reply(task: ForwardTask, message: Message) -> Optional[int]:
    if not task.forward_replies:
        return None

    replied = message.reply_to_message
    if not replied:
        replied_id = getattr(message, "reply_to_message_id", None)
        if replied_id is None:
            replied_id = getattr(message, "reply_to_top_message_id", None)
        if replied_id is None:
            return None
    else:
        replied_id = replied.id

    key = resolve_history_key(task)
    history = FORWARD_HISTORY.get(key)
    if not history:
        return None

    for original_id, forwarded_id in reversed(history):
        if original_id == replied_id:
            return forwarded_id
    return None


def message_category(message: Message) -> str:
    if message.text and not message.media:
        return "text"
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.audio:
        return "audio"
    if message.voice:
        return "voice"
    if message.video_note:
        return "video"
    if message.document:
        return "document"
    if message.animation:
        return "animation"
    if message.sticker:
        return "sticker"
    return "other"


def get_message_media_size(message: Message) -> Optional[int]:
    media = (
        message.document
        or message.video
        or message.audio
        or message.voice
        or message.video_note
        or message.animation
        or message.sticker
        or message.photo
    )
    if not media:
        return None
    return getattr(media, "file_size", None)


def within_size_limits(message: Message, task: ForwardTask) -> bool:
    min_size = task.min_media_size
    max_size = task.max_media_size
    if min_size is None and max_size is None:
        return True

    file_size = get_message_media_size(message)
    if file_size is None:
        return True

    if min_size is not None and file_size < min_size:
        return False
    if max_size is not None and file_size > max_size:
        return False
    return True


def matches_media_filter(message: Message, task: ForwardTask) -> bool:
    media_types = task.media_types or []
    if not media_types:
        return False
    if "all" not in media_types:
        category = message_category(message)
        if category == "other":
            return False
        if category not in media_types:
            return False
    return within_size_limits(message, task)


def build_caption(message: Message, task: ForwardTask) -> Optional[str]:
    if not task.caption:
        return message.caption

    original_caption = message.caption
    if message.text and not message.media:
        original_caption = message.text

    if original_caption:
        return f"{task.caption}\n\n{original_caption}".strip()
    return task.caption


def sanitize_text(text: Optional[str], task: ForwardTask) -> Optional[str]:
    if not text:
        return text
    if not task.remove_links:
        return text

    cleaned = URL_PATTERN.sub("", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" ?\n ?", "\n", cleaned)
    cleaned = cleaned.strip()
    return cleaned or None


async def send_forward(client: Client, message: Message, task: ForwardTask) -> Optional[Message]:
    if not matches_media_filter(message, task):
        return None

    signature = dedupe_signature(message) if task.skip_duplicates else None
    if signature and has_seen_duplicate(task.task_id, signature):
        return None

    reply_to = find_forwarded_reply(task, message)
    caption = sanitize_text(build_caption(message, task), task)

    try:
        if message.text and not message.media:
            if caption is not None:
                text = caption
            else:
                text = sanitize_text(message.text, task) or ""
            if not text.strip():
                return None
            sent = await client.send_message(
                task.target_id, text, reply_to_message_id=reply_to
            )
        else:
            kwargs = {"reply_to_message_id": reply_to}
            if caption:
                kwargs["caption"] = caption
            sent = await message.copy(task.target_id, **kwargs)
    except RPCError as err:
        logger.exception("Failed to forward message %s: %s", message.id, err)
        return None

    register_forwarded_message(task, message, sent)
    if signature:
        remember_duplicate_signature(task.task_id, signature)
    return sent


def human_readable_size(value: int) -> str:
    size = float(value)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            formatted = f"{size:.2f}".rstrip("0").rstrip(".")
            return f"{formatted} {unit}"
        size /= 1024
    return f"{int(size)} B"


def format_size_value(value: int) -> str:
    if value == DEFAULT_MAX_MEDIA_SIZE:
        return f"{DEFAULT_MAX_MEDIA_SIZE_MB} MB"
    return human_readable_size(value)


def format_size_range(min_size: Optional[int], max_size: Optional[int]) -> str:
    if min_size is None and max_size is None:
        return "Any size"
    if min_size is not None and max_size is not None:
        return f"{format_size_value(min_size)} – {format_size_value(max_size)}"
    if min_size is not None:
        return f"≥ {format_size_value(min_size)}"
    if max_size is not None:
        return f"≤ {format_size_value(max_size)}"
    return "Any size"


def parse_size_limits(text: str) -> Tuple[Optional[int], Optional[int]]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Empty size input")
    if cleaned == "-":
        return None, None

    normalized = cleaned.lower().replace(" ", "")
    if "to" in normalized:
        normalized = normalized.replace("to", "-")

    if "-" in normalized:
        min_part, max_part = normalized.split("-", 1)
    elif "," in normalized:
        min_part, max_part = normalized.split(",", 1)
    else:
        min_part, max_part = "", normalized

    def parse_part(part: str) -> float:
        if not part:
            return 0.0
        multiplier = 1.0
        if part.endswith("kb"):
            multiplier = 1.0 / 1024
            part = part[:-2]
        elif part.endswith("mb"):
            multiplier = 1.0
            part = part[:-2]
        elif part.endswith("gb"):
            multiplier = 1024.0
            part = part[:-2]
        elif part.endswith("b"):
            multiplier = 1.0 / BYTES_IN_MB
            part = part[:-1]
        return float(part or 0) * multiplier

    try:
        min_value = parse_part(min_part)
        max_value = parse_part(max_part) if max_part else None
    except ValueError as err:
        raise ValueError("Invalid size value") from err

    if min_value < 0 or (max_value is not None and max_value < 0):
        raise ValueError("Size values must be non-negative")

    min_bytes = int(min_value * BYTES_IN_MB) if min_value > 0 else None
    max_bytes = (
        int(max_value * BYTES_IN_MB) if max_value is not None and max_value > 0 else None
    )

    if min_bytes is not None and max_bytes is not None and min_bytes > max_bytes:
        raise ValueError("Minimum size cannot exceed maximum size")

    return min_bytes, max_bytes


def render_task(task: ForwardTask) -> str:
    if not task.media_types or "all" in task.media_types:
        selected = MEDIA_FILTER_OPTIONS
    else:
        selected = task.media_types

    media_description = describe_selected_media(selected)
    size_text = format_size_range(task.min_media_size, task.max_media_size)
    skip_status = "✅ 𝙾𝚗" if task.skip_duplicates else "❌ 𝙾𝚏𝚏"
    link_status = "✅ 𝙾𝚗" if task.remove_links else "❌ 𝙾𝚏𝚏"
    caption = html.escape(task.caption) if task.caption else "<i>𝙽𝚘𝚝 𝚜𝚎𝚝</i>"

    return TASK_CARD.format(
        id=task.task_id,
        source_title=html.escape(task.source_name),
        source_id=task.source_id,
        target_title=html.escape(task.target_name),
        target_id=task.target_id,
        media=media_description,
        size_limit=html.escape(size_text),
        skip_status=skip_status,
        link_status=link_status,
        caption=caption,
    )
