"""Channel message handlers for automation features."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Deque, Dict, List, Optional, Tuple

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from db import get_channel, get_channel_settings, log_action

RecentEntry = Dict[str, Any]

recent_channel_cache: Dict[int, Deque[Dict[str, Any]]] = defaultdict(deque)
owner_recent_cache: Dict[int, Deque[Dict[str, Any]]] = defaultdict(deque)
reply_tracker: Dict[Tuple[int, int], Deque[Dict[str, Any]]] = defaultdict(deque)
admin_cache: Dict[Tuple[int, int], bool] = {}
MAX_CACHE = 500


async def channel_message_handler(client: Client, message: Message) -> None:
    if not message.chat or message.service:
        return
    channel_doc = get_channel(message.chat.id)
    if not channel_doc:
        return
    settings = get_channel_settings(message.chat.id)
    if not settings:
        return
    owner_id = channel_doc["owner_user_id"]
    deleted = await process_duplicates(client, message, channel_doc, settings, owner_id)
    if deleted:
        return
    await process_replies(client, message, channel_doc, settings)
    await process_auto_caption(client, message, channel_doc, settings)
    await process_auto_reactions(client, message, channel_doc, settings)


async def process_duplicates(client: Client, message: Message, channel: Dict[str, Any], settings: Dict[str, Any], owner_id: int) -> bool:
    cfg = settings.get("duplicates", {})
    if not cfg.get("enabled"):
        _store_recent_message(message, owner_id)
        return False
    info = _extract_message_info(message)
    candidates = _get_candidate_messages(channel["channel_id"], owner_id, cfg)
    matched = _find_duplicate_match(info, candidates, cfg)
    if matched:
        strategy = cfg.get("strategy", "delete_new")
        if strategy == "delete_new":
            await client.delete_messages(message.chat.id, message.id)
            log_action(message.chat.id, owner_id, "duplicate_deleted", {"message_id": message.id, "reason": matched[1]})
            return True
        else:
            await client.delete_messages(matched[0]["channel_id"], matched[0]["message_id"])
            _remove_from_cache(matched[0]["channel_id"], owner_id, matched[0]["message_id"])
            log_action(message.chat.id, owner_id, "duplicate_old_deleted", {"message_id": matched[0]["message_id"], "reason": matched[1]})
    _store_recent_message(message, owner_id)
    return False


async def process_replies(client: Client, message: Message, channel: Dict[str, Any], settings: Dict[str, Any]) -> None:
    cfg = settings.get("replies", {})
    if not cfg.get("enabled") or not message.reply_to_message_id:
        return
    key = (channel["channel_id"], message.reply_to_message_id)
    ignore_admin = cfg.get("ignore_admin_replies", True)
    is_admin = False
    if ignore_admin and message.from_user:
        is_admin = await _is_admin(client, channel["channel_id"], message.from_user.id)
    entry = {
        "message_id": message.id,
        "from_user_id": message.from_user.id if message.from_user else None,
        "is_admin": is_admin,
        "date": message.date,
    }
    tracker = reply_tracker[key]
    tracker.append(entry)
    if len(tracker) > MAX_CACHE:
        tracker.popleft()
    mode = cfg.get("mode", "keep_latest")
    to_delete: List[int] = []
    now = datetime.utcnow()
    if mode == "keep_latest":
        for prev in list(tracker)[:-1]:
            if ignore_admin and prev["is_admin"]:
                continue
            to_delete.append(prev["message_id"])
    elif mode == "delete_all_after_time":
        limit = cfg.get("time_limit_minutes", 60)
        root_date = message.reply_to_message.date if message.reply_to_message else message.date
        if (now - root_date) > timedelta(minutes=limit) and not (ignore_admin and is_admin):
            to_delete.append(message.id)
        for prev in list(tracker):
            if prev is entry:
                continue
            if (now - prev["date"]) > timedelta(minutes=limit) and not (ignore_admin and prev["is_admin"]):
                to_delete.append(prev["message_id"])
    elif mode == "delete_if_count_gt_n":
        max_count = max(1, cfg.get("max_replies", 3))
        candidates = [p for p in tracker if not (ignore_admin and p["is_admin"])]
        while len(candidates) > max_count:
            victim = candidates.pop(0)
            to_delete.append(victim["message_id"])
    if to_delete:
        await client.delete_messages(channel["channel_id"], to_delete)
        tracker = deque([p for p in tracker if p["message_id"] not in to_delete], maxlen=MAX_CACHE)
        reply_tracker[key] = tracker
        log_action(channel["channel_id"], channel["owner_user_id"], "reply_cleanup", {"deleted": to_delete})


async def process_auto_caption(client: Client, message: Message, channel: Dict[str, Any], settings: Dict[str, Any]) -> None:
    cfg = settings.get("caption", {})
    if not cfg.get("enabled"):
        return
    apply_to = cfg.get("apply_to", [])
    has_media = message.media is not None
    is_text_post = bool(message.text) and not has_media
    target_media = has_media and ("media" in apply_to)
    target_text = is_text_post and ("text" in apply_to)
    if not target_media and not target_text:
        return
    template = cfg.get("template") or ""
    if not template:
        return
    new_caption = _render_caption(template, message, channel)
    behavior = cfg.get("on_existing_caption", "append")
    try:
        if has_media and target_media:
            existing = message.caption or ""
            updated = _merge_caption(existing, new_caption, behavior)
            if updated is None:
                return
            await client.edit_message_caption(message.chat.id, message.id, updated)
        elif target_text:
            existing = message.text or ""
            updated = _merge_caption(existing, new_caption, behavior)
            if updated is None:
                return
            await client.edit_message_text(message.chat.id, message.id, updated)
        log_action(message.chat.id, channel["owner_user_id"], "caption_applied", {"message_id": message.id})
    except Exception:
        return


async def process_auto_reactions(client: Client, message: Message, channel: Dict[str, Any], settings: Dict[str, Any]) -> None:
    cfg = settings.get("reactions", {})
    if not cfg.get("enabled"):
        return
    scope = cfg.get("scope", "all")
    has_media = message.media is not None
    if scope == "media_only" and not has_media:
        return
    if scope == "admin_posts_only":
        sender_is_admin = False
        if message.sender_chat and message.sender_chat.id == message.chat.id:
            sender_is_admin = True
        elif message.from_user:
            sender_is_admin = await _is_admin(client, message.chat.id, message.from_user.id)
        if not sender_is_admin:
            return
    emojis = cfg.get("emojis", [])
    for emoji in emojis:
        try:
            await client.send_reaction(message.chat.id, message.id, emoji)
        except Exception:
            continue
    if emojis:
        log_action(message.chat.id, channel["owner_user_id"], "reactions_added", {"message_id": message.id, "emojis": emojis})


def _extract_message_info(message: Message) -> Dict[str, Any]:
    text_content = (message.text or message.caption or "").strip().lower()
    caption_text = (message.caption or "").strip().lower()
    media_id = _get_media_file_id(message)
    return {
        "channel_id": message.chat.id,
        "message_id": message.id,
        "text": text_content,
        "caption": caption_text,
        "media_file_id": media_id,
        "date": message.date,
    }


def _get_media_file_id(message: Message) -> Optional[str]:
    fields = [
        "photo",
        "animation",
        "audio",
        "document",
        "video",
        "video_note",
        "voice",
        "sticker",
    ]
    for field in fields:
        value = getattr(message, field, None)
        if value:
            return value.file_id
    return None


def _store_recent_message(message: Message, owner_id: int) -> None:
    info = _extract_message_info(message)
    channel_deque = recent_channel_cache[message.chat.id]
    channel_deque.append(info)
    if len(channel_deque) > MAX_CACHE:
        channel_deque.popleft()
    owner_deque = owner_recent_cache[owner_id]
    owner_deque.append(info)
    if len(owner_deque) > MAX_CACHE:
        owner_deque.popleft()


def _get_candidate_messages(channel_id: int, owner_id: int, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    if cfg.get("scope") == "global":
        deq = owner_recent_cache[owner_id]
    else:
        deq = recent_channel_cache[channel_id]
    _trim_deque(deq, cfg)
    return list(deq)


def _trim_deque(deq: Deque[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    window_type = cfg.get("window_type", "messages")
    window_value = max(1, int(cfg.get("window_value", 20)))
    if window_type == "messages":
        while len(deq) > window_value:
            deq.popleft()
    else:
        cutoff = datetime.utcnow() - timedelta(minutes=window_value)
        while deq and deq[0]["date"] < cutoff:
            deq.popleft()


def _find_duplicate_match(info: Dict[str, Any], candidates: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], str]]:
    criteria = cfg.get("criteria", [])
    for candidate in reversed(candidates):
        for criterion in criteria:
            if _matches_criterion(info, candidate, criterion):
                return candidate, criterion
    return None


def _matches_criterion(info: Dict[str, Any], candidate: Dict[str, Any], criterion: str) -> bool:
    if criterion == "text":
        return bool(info["text"]) and info["text"] == candidate.get("text")
    if criterion == "caption":
        return bool(info["caption"]) and info["caption"] == candidate.get("caption")
    if criterion == "media_file_id":
        return bool(info["media_file_id"]) and info["media_file_id"] == candidate.get("media_file_id")
    if criterion == "fuzzy_text":
        if not info["text"] or not candidate.get("text"):
            return False
        ratio = SequenceMatcher(None, info["text"], candidate.get("text", "")).ratio()
        return ratio >= 0.9
    return False


def _remove_from_cache(channel_id: int, owner_id: int, message_id: int) -> None:
    channel_deque = recent_channel_cache[channel_id]
    for idx, item in enumerate(list(channel_deque)):
        if item["message_id"] == message_id:
            del channel_deque[idx]
            break
    owner_deque = owner_recent_cache[owner_id]
    for idx, item in enumerate(list(owner_deque)):
        if item["message_id"] == message_id and item["channel_id"] == channel_id:
            del owner_deque[idx]
            break


def _render_caption(template: str, message: Message, channel: Dict[str, Any]) -> str:
    username = channel.get("channel_username")
    replacements = {
        "{channel_title}": channel.get("title", ""),
        "{channel_username}": f"@{username}" if username else "",
        "{message_id}": str(message.id),
        "{date}": message.date.strftime("%Y-%m-%d"),
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def _merge_caption(existing: str, template: str, behavior: str) -> Optional[str]:
    existing = existing or ""
    if behavior == "skip" and existing:
        return None
    if behavior == "replace" or not existing:
        return template
    if behavior == "append":
        return f"{existing}\n{template}".strip()
    return template


async def _is_admin(client: Client, channel_id: int, user_id: int) -> bool:
    key = (channel_id, user_id)
    if key in admin_cache:
        return admin_cache[key]
    member = await client.get_chat_member(channel_id, user_id)
    is_admin = member.status in ("administrator", "creator")
    admin_cache[key] = is_admin
    return is_admin


def register(app: Client) -> None:
    app.add_handler(
        MessageHandler(
            channel_message_handler,
            filters.channel & ~filters.service,
        )
    )
