"""Command handlers for the channel management bot."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from db import (
    add_channel,
    get_channel_settings,
    get_or_create_user,
    list_channels,
    remove_channel,
    update_channel_settings,
)

ConversationHandler = Callable[[Client, Message, Dict[str, Any]], Any]


class ConversationManager:
    """A simple in-memory conversation tracker."""

    def __init__(self) -> None:
        self._states: Dict[int, Dict[str, Any]] = {}

    def start(self, user_id: int, handler: ConversationHandler, context: Optional[Dict[str, Any]] = None) -> None:
        self._states[user_id] = {
            "handler": handler,
            "context": context or {},
        }

    def stop(self, user_id: int) -> None:
        self._states.pop(user_id, None)

    def set_next(self, user_id: int, handler: ConversationHandler) -> None:
        if user_id in self._states:
            self._states[user_id]["handler"] = handler

    def get_context(self, user_id: int) -> Dict[str, Any]:
        state = self._states.get(user_id)
        if not state:
            return {}
        return state["context"]

    async def process(self, client: Client, message: Message) -> bool:
        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return False
        state = self._states.get(user_id)
        if not state:
            return False
        handler = state.get("handler")
        if not handler:
            return False
        await handler(client, message, state)
        return True


conversation_manager = ConversationManager()


async def _get_bot_id(client: Client) -> int:
    me = getattr(client, "me", None)
    if me is None:
        me = await client.get_me()
    return me.id


async def _ensure_user_admin(client: Client, channel_id: int, user_id: int) -> None:
    member = await client.get_chat_member(channel_id, user_id)
    if member.status not in ("administrator", "creator"):
        raise ValueError("You must be an administrator of that channel to manage it.")


async def _ensure_bot_permissions(client: Client, channel_id: int) -> None:
    bot_id = await _get_bot_id(client)
    member = await client.get_chat_member(channel_id, bot_id)
    privileges = getattr(member, "privileges", None)
    missing: List[str] = []
    if not privileges:
        missing.append("administrator access")
    else:
        if not getattr(privileges, "can_delete_messages", False):
            missing.append("delete messages")
        if not getattr(privileges, "can_edit_messages", False):
            missing.append("edit messages")
        if not getattr(privileges, "can_post_messages", True):
            missing.append("post messages")
    if missing:
        raise ValueError(
            "The bot must be admin with permissions to " + ", ".join(missing)
        )


async def _ensure_user_and_bot_permissions(client: Client, channel_id: int, user_id: int) -> None:
    await _ensure_user_admin(client, channel_id, user_id)
    await _ensure_bot_permissions(client, channel_id)


def _format_channel_line(channel: Dict[str, Any], settings: Dict[str, Any]) -> str:
    dup = "ON" if settings.get("duplicates", {}).get("enabled") else "OFF"
    rep = "ON" if settings.get("replies", {}).get("enabled") else "OFF"
    cap = "ON" if settings.get("caption", {}).get("enabled") else "OFF"
    react = "ON" if settings.get("reactions", {}).get("enabled") else "OFF"
    username = channel.get("channel_username")
    readable = f"{channel['title']} ({'@' + username if username else channel['channel_id']})"
    return f"{readable}\n- Duplicates: {dup} | Replies: {rep} | Caption: {cap} | Reactions: {react}"


def _parse_channel_selection(text: str, channels: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(channels):
            return channels[idx]
    for channel in channels:
        if text == str(channel["channel_id"]):
            return channel
        username = channel.get("channel_username")
        if username and text.lstrip("@") == username.lstrip("@"):
            return channel
    return None


async def _ensure_access_or_notify(client: Client, message: Message, channel: Dict[str, Any]) -> bool:
    try:
        await _ensure_user_and_bot_permissions(client, channel["channel_id"], message.from_user.id)
        return True
    except ValueError as exc:
        await message.reply_text(str(exc))
        conversation_manager.stop(message.from_user.id)
        return False


async def cmd_start(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user = message.from_user
    get_or_create_user(user.id, user.first_name, user.username)
    text = (
        "👋 **Welcome to the Channel Management Bot!**\n\n"
        "Add me as an administrator to your channels and use /addchannel here in DM to link them. "
        "Once connected, I can clean duplicates, moderate replies, add captions, and drop reactions automatically."
    )
    await message.reply_text(text)


async def cmd_help(_: Client, message: Message) -> None:
    text = (
        "**Available Commands**\n\n"
        "/start – Welcome message and quick intro.\n"
        "/help – Show this help.\n"
        "/addchannel – Connect a new channel.\n"
        "/listchannels – Show your managed channels.\n"
        "/removechannel – Disconnect a channel.\n"
        "/settings – Interactive settings menu.\n"
        "/dup_settings – Configure duplicate cleaner.\n"
        "/reply_settings – Configure reply cleanup.\n"
        "/caption_settings – Configure auto captions.\n"
        "/reaction_settings – Configure reactions.\n"
        "/status – Display channel status summary."
    )
    await message.reply_text(text)


async def cmd_listchannels(_: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("You do not have any channels linked. Use /addchannel to add one.")
        return
    response_lines: List[str] = []
    for idx, channel in enumerate(channels_docs, start=1):
        settings = get_channel_settings(channel["channel_id"]) or {}
        response_lines.append(f"{idx}. {_format_channel_line(channel, settings)}")
    await message.reply_text("\n\n".join(response_lines))


async def cmd_addchannel(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user = message.from_user
    get_or_create_user(user.id, user.first_name, user.username)
    await message.reply_text(
        "Please forward a message from the target channel or send its @username / ID."
    )
    conversation_manager.start(
        user.id,
        _handle_addchannel_input,
        {"user_id": user.id},
    )


async def _handle_addchannel_input(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = state["context"]["user_id"]
    channel = await _resolve_channel_from_message(client, message)
    if not channel:
        await message.reply_text("I could not understand that channel. Please try again.")
        return
    try:
        await _ensure_user_and_bot_permissions(client, channel.id, user_id)
    except ValueError as exc:
        await message.reply_text(str(exc))
        conversation_manager.stop(user_id)
        return
    add_channel(
        user_id,
        channel.id,
        channel.username,
        channel.title or "Unnamed channel",
    )
    await message.reply_text(
        f"✅ Channel **{channel.title}** has been linked. Configure it using /settings."
    )
    conversation_manager.stop(user_id)


async def _resolve_channel_from_message(client: Client, message: Message):
    if message.forward_from_chat and message.forward_from_chat.type == "channel":
        return message.forward_from_chat
    text = message.text or message.caption or ""
    if not text:
        return None
    text = text.strip()
    if text.startswith("@"):
        identifier: Any = text
    else:
        identifier = text
    try:
        chat = await client.get_chat(identifier)
    except RPCError:
        return None
    if chat.type != "channel":
        return None
    return chat


async def cmd_removechannel(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("No channels found. Use /addchannel first.")
        return
    text_lines = [
        "Send the number or ID of the channel you want to remove:",
    ]
    for idx, channel in enumerate(channels_docs, start=1):
        text_lines.append(f"{idx}. {channel['title']} ({channel['channel_id']})")
    await message.reply_text("\n".join(text_lines))
    conversation_manager.start(
        user_id,
        _handle_remove_channel_selection,
        {"channels": channels_docs},
    )


async def _handle_remove_channel_selection(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channels_docs = state["context"]["channels"]
    selection = _parse_channel_selection(message.text or "", channels_docs)
    if not selection:
        await message.reply_text("Invalid selection. Try again.")
        return
    if not await _ensure_access_or_notify(client, message, selection):
        return
    removed = remove_channel(user_id, selection["channel_id"])
    if removed:
        await message.reply_text(
            f"Channel {selection['title']} has been removed."
        )
    else:
        await message.reply_text("I could not remove that channel. Make sure you are the owner.")
    conversation_manager.stop(user_id)


async def cmd_settings(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("You have no channels configured.")
        return
    await message.reply_text(
        "Choose a channel by sending its number or ID:\n" +
        "\n".join(
            f"{idx}. {c['title']} ({c.get('channel_username') or c['channel_id']})"
            for idx, c in enumerate(channels_docs, start=1)
        )
    )
    conversation_manager.start(
        user_id,
        _handle_settings_channel_choice,
        {"channels": channels_docs, "step": "channel"},
    )


async def _handle_settings_channel_choice(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channels_docs = state["context"]["channels"]
    selection = _parse_channel_selection(message.text or "", channels_docs)
    if not selection:
        await message.reply_text("Invalid selection. Try again.")
        return
    if not await _ensure_access_or_notify(client, message, selection):
        return
    state["context"]["channel"] = selection
    menu = (
        "Selected channel: **{title}**\n\n"
        "Reply with a number:\n"
        "1. Duplicate cleaner settings\n"
        "2. Reply cleanup settings\n"
        "3. Auto-caption settings\n"
        "4. Auto-reaction settings\n"
        "5. Show status summary"
    ).format(title=selection["title"])
    await message.reply_text(menu)
    conversation_manager.set_next(user_id, _handle_settings_menu_choice)


async def _handle_settings_menu_choice(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channel = state["context"]["channel"]
    choice = (message.text or "").strip()
    if choice not in {"1", "2", "3", "4", "5"}:
        await message.reply_text("Please send a number between 1 and 5.")
        return
    conversation_manager.stop(user_id)
    if choice == "1":
        await start_duplicate_settings_flow(client, message, channel)
    elif choice == "2":
        await start_reply_settings_flow(client, message, channel)
    elif choice == "3":
        await start_caption_settings_flow(client, message, channel)
    elif choice == "4":
        await start_reaction_settings_flow(client, message, channel)
    else:
        await show_status_summary(message, channel)


async def cmd_dup_settings(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("You do not have channels registered.")
        return
    await message.reply_text(
        "Choose a channel to configure duplicate cleaner:\n" +
        "\n".join(
            f"{idx}. {c['title']} ({c.get('channel_username') or c['channel_id']})"
            for idx, c in enumerate(channels_docs, start=1)
        )
    )
    conversation_manager.start(
        user_id,
        _handle_dup_select_channel,
        {"channels": channels_docs},
    )


async def start_duplicate_settings_flow(client: Client, message: Message, channel: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    if not await _ensure_access_or_notify(client, message, channel):
        return
    await message.reply_text(
        f"Duplicate cleaner for **{channel['title']}** — send `on` or `off`."
    )
    conversation_manager.start(
        user_id,
        _handle_dup_toggle,
        {"channel": channel},
    )


async def _handle_dup_select_channel(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    selection = _parse_channel_selection(message.text or "", state["context"]["channels"])
    if not selection:
        await message.reply_text("Invalid selection, try again.")
        return
    await start_duplicate_settings_flow(client, message, selection)


async def _handle_dup_toggle(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channel = state["context"]["channel"]
    answer = (message.text or "").strip().lower()
    if answer not in {"on", "off"}:
        await message.reply_text("Please respond with `on` or `off`.")
        return
    state["context"]["enabled"] = answer == "on"
    if not state["context"]["enabled"]:
        update_channel_settings(channel["channel_id"], {"duplicates.enabled": False})
        await message.reply_text("Duplicate cleaner disabled.")
        conversation_manager.stop(user_id)
        return
    await message.reply_text(
        "Select criteria (comma separated numbers):\n"
        "1) Same text\n2) Same media file\n3) Same caption\n4) Fuzzy text"
    )
    conversation_manager.set_next(user_id, _handle_dup_criteria)


async def _handle_dup_criteria(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    choices = [c.strip() for c in (message.text or "").split(",") if c.strip()]
    mapping = {"1": "text", "2": "media_file_id", "3": "caption", "4": "fuzzy_text"}
    selected = [mapping[c] for c in choices if c in mapping]
    if not selected:
        await message.reply_text("Please send numbers like `1,2`.")
        return
    state["context"]["criteria"] = selected
    await message.reply_text("Scope? Type `channel` or `global`.")
    conversation_manager.set_next(user_id, _handle_dup_scope)


async def _handle_dup_scope(client: Client, message: Message, state: Dict[str, Any]) -> None:
    answer = (message.text or "").strip().lower()
    if answer not in {"channel", "global"}:
        await message.reply_text("Reply with `channel` or `global`.")
        return
    state["context"]["scope"] = answer
    await message.reply_text("Window type? `messages` or `minutes`.")
    conversation_manager.set_next(message.from_user.id, _handle_dup_window_type)


async def _handle_dup_window_type(client: Client, message: Message, state: Dict[str, Any]) -> None:
    answer = (message.text or "").strip().lower()
    if answer not in {"messages", "minutes"}:
        await message.reply_text("Reply with `messages` or `minutes`.")
        return
    state["context"]["window_type"] = answer
    await message.reply_text("Enter a numeric window value (e.g. 50).")
    conversation_manager.set_next(message.from_user.id, _handle_dup_window_value)


async def _handle_dup_window_value(client: Client, message: Message, state: Dict[str, Any]) -> None:
    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.reply_text("Enter a number like 50.")
        return
    state["context"]["window_value"] = value
    await message.reply_text("Strategy? `delete_new` or `delete_old`.")
    conversation_manager.set_next(message.from_user.id, _handle_dup_strategy)


async def _handle_dup_strategy(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    answer = (message.text or "").strip().lower()
    if answer not in {"delete_new", "delete_old"}:
        await message.reply_text("Reply with `delete_new` or `delete_old`.")
        return
    state["context"]["strategy"] = answer
    channel = state["context"]["channel"]
    update = {
        "duplicates": {
            "enabled": True,
            "criteria": state["context"]["criteria"],
            "scope": state["context"]["scope"],
            "window_type": state["context"]["window_type"],
            "window_value": state["context"]["window_value"],
            "strategy": state["context"]["strategy"],
        }
    }
    update_channel_settings(channel["channel_id"], update)
    await message.reply_text(
        f"Duplicates enabled with criteria {', '.join(update['duplicates']['criteria'])}."
    )
    conversation_manager.stop(user_id)


async def cmd_reply_settings(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("No channels found.")
        return
    await message.reply_text(
        "Choose a channel to configure reply cleanup:\n" +
        "\n".join(
            f"{idx}. {c['title']} ({c.get('channel_username') or c['channel_id']})"
            for idx, c in enumerate(channels_docs, start=1)
        )
    )
    conversation_manager.start(
        user_id,
        _handle_reply_select_channel,
        {"channels": channels_docs},
    )


async def start_reply_settings_flow(client: Client, message: Message, channel: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    if not await _ensure_access_or_notify(client, message, channel):
        return
    await message.reply_text(f"Reply cleanup for **{channel['title']}** — `on` or `off`?")
    conversation_manager.start(
        user_id,
        _handle_reply_toggle,
        {"channel": channel},
    )


async def _handle_reply_select_channel(client: Client, message: Message, state: Dict[str, Any]) -> None:
    selection = _parse_channel_selection(message.text or "", state["context"]["channels"])
    if not selection:
        await message.reply_text("Invalid selection.")
        return
    await start_reply_settings_flow(client, message, selection)


async def _handle_reply_toggle(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channel = state["context"]["channel"]
    answer = (message.text or "").strip().lower()
    if answer not in {"on", "off"}:
        await message.reply_text("Answer `on` or `off`.")
        return
    state["context"]["enabled"] = answer == "on"
    if not state["context"]["enabled"]:
        update_channel_settings(channel["channel_id"], {"replies.enabled": False})
        await message.reply_text("Reply cleanup disabled.")
        conversation_manager.stop(user_id)
        return
    await message.reply_text(
        "Choose mode:\n1) keep_latest\n2) delete_all_after_time\n3) delete_if_count_gt_n"
    )
    conversation_manager.set_next(user_id, _handle_reply_mode)


async def _handle_reply_mode(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    mapping = {"1": "keep_latest", "2": "delete_all_after_time", "3": "delete_if_count_gt_n"}
    mode = mapping.get((message.text or "").strip())
    if not mode:
        await message.reply_text("Please send 1, 2 or 3.")
        return
    state["context"]["mode"] = mode
    if mode == "delete_all_after_time":
        await message.reply_text("Enter time limit in minutes (e.g. 30).")
        conversation_manager.set_next(user_id, _handle_reply_time_limit)
        return
    if mode == "delete_if_count_gt_n":
        await message.reply_text("Enter maximum replies to keep (e.g. 5).")
        conversation_manager.set_next(user_id, _handle_reply_max_replies)
        return
    await message.reply_text("Ignore admin replies? (yes/no)")
    conversation_manager.set_next(user_id, _handle_reply_ignore_admin)


async def _handle_reply_time_limit(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    try:
        minutes = int((message.text or "").strip())
    except ValueError:
        await message.reply_text("Send a number of minutes.")
        return
    state["context"]["time_limit_minutes"] = minutes
    await message.reply_text("Ignore admin replies? (yes/no)")
    conversation_manager.set_next(user_id, _handle_reply_ignore_admin)


async def _handle_reply_max_replies(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    try:
        max_replies = int((message.text or "").strip())
    except ValueError:
        await message.reply_text("Send a number like 5.")
        return
    state["context"]["max_replies"] = max_replies
    await message.reply_text("Ignore admin replies? (yes/no)")
    conversation_manager.set_next(user_id, _handle_reply_ignore_admin)


async def _handle_reply_ignore_admin(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    answer = (message.text or "").strip().lower()
    if answer not in {"yes", "no"}:
        await message.reply_text("Reply with yes or no.")
        return
    channel = state["context"]["channel"]
    update = {
        "replies": {
            "enabled": True,
            "mode": state["context"].get("mode", "keep_latest"),
            "time_limit_minutes": state["context"].get("time_limit_minutes", 60),
            "max_replies": state["context"].get("max_replies", 3),
            "ignore_admin_replies": answer == "yes",
        }
    }
    update_channel_settings(channel["channel_id"], update)
    await message.reply_text("Reply cleanup updated.")
    conversation_manager.stop(user_id)


async def cmd_caption_settings(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("No channels configured.")
        return
    await message.reply_text(
        "Choose a channel for captions:\n" +
        "\n".join(
            f"{idx}. {c['title']} ({c.get('channel_username') or c['channel_id']})"
            for idx, c in enumerate(channels_docs, start=1)
        )
    )
    conversation_manager.start(
        user_id,
        _handle_caption_select_channel,
        {"channels": channels_docs},
    )


async def start_caption_settings_flow(client: Client, message: Message, channel: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    if not await _ensure_access_or_notify(client, message, channel):
        return
    await message.reply_text(f"Auto caption for **{channel['title']}** — `on` or `off`?")
    conversation_manager.start(
        user_id,
        _handle_caption_toggle,
        {"channel": channel},
    )


async def _handle_caption_select_channel(client: Client, message: Message, state: Dict[str, Any]) -> None:
    selection = _parse_channel_selection(message.text or "", state["context"]["channels"])
    if not selection:
        await message.reply_text("Invalid selection.")
        return
    await start_caption_settings_flow(client, message, selection)


async def _handle_caption_toggle(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channel = state["context"]["channel"]
    answer = (message.text or "").strip().lower()
    if answer not in {"on", "off"}:
        await message.reply_text("Reply `on` or `off`.")
        return
    state["context"]["enabled"] = answer == "on"
    if not state["context"]["enabled"]:
        update_channel_settings(channel["channel_id"], {"caption.enabled": False})
        await message.reply_text("Auto caption disabled.")
        conversation_manager.stop(user_id)
        return
    await message.reply_text("Apply to? (1 media / 2 text / 3 both)")
    conversation_manager.set_next(user_id, _handle_caption_apply_to)


async def _handle_caption_apply_to(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    mapping = {"1": ["media"], "2": ["text"], "3": ["media", "text"]}
    apply_to = mapping.get((message.text or "").strip())
    if not apply_to:
        await message.reply_text("Send 1, 2 or 3.")
        return
    state["context"]["apply_to"] = apply_to
    await message.reply_text("If existing caption exists: `append`, `replace`, or `skip`?")
    conversation_manager.set_next(user_id, _handle_caption_existing_behavior)


async def _handle_caption_existing_behavior(client: Client, message: Message, state: Dict[str, Any]) -> None:
    answer = (message.text or "").strip().lower()
    if answer not in {"append", "replace", "skip"}:
        await message.reply_text("Choose append, replace, or skip.")
        return
    state["context"]["on_existing"] = answer
    await message.reply_text(
        "Send the caption template. You can use {channel_title}, {channel_username}, {message_id}, {date}."
    )
    conversation_manager.set_next(message.from_user.id, _handle_caption_template)


async def _handle_caption_template(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    template = message.text or message.caption
    if not template:
        await message.reply_text("Template cannot be empty.")
        return
    channel = state["context"]["channel"]
    update = {
        "caption": {
            "enabled": True,
            "apply_to": state["context"]["apply_to"],
            "on_existing_caption": state["context"]["on_existing"],
            "template": template,
        }
    }
    update_channel_settings(channel["channel_id"], update)
    await message.reply_text("Caption template saved.")
    conversation_manager.stop(user_id)


async def cmd_reaction_settings(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("No channels configured.")
        return
    await message.reply_text(
        "Choose a channel for auto reactions:\n" +
        "\n".join(
            f"{idx}. {c['title']} ({c.get('channel_username') or c['channel_id']})"
            for idx, c in enumerate(channels_docs, start=1)
        )
    )
    conversation_manager.start(
        user_id,
        _handle_reaction_select_channel,
        {"channels": channels_docs},
    )


async def start_reaction_settings_flow(client: Client, message: Message, channel: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    if not await _ensure_access_or_notify(client, message, channel):
        return
    await message.reply_text(f"Auto reactions for **{channel['title']}** — `on` or `off`?")
    conversation_manager.start(
        user_id,
        _handle_reaction_toggle,
        {"channel": channel},
    )


async def _handle_reaction_select_channel(client: Client, message: Message, state: Dict[str, Any]) -> None:
    selection = _parse_channel_selection(message.text or "", state["context"]["channels"])
    if not selection:
        await message.reply_text("Invalid selection.")
        return
    await start_reaction_settings_flow(client, message, selection)


async def _handle_reaction_toggle(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    channel = state["context"]["channel"]
    answer = (message.text or "").strip().lower()
    if answer not in {"on", "off"}:
        await message.reply_text("Reply `on` or `off`.")
        return
    state["context"]["enabled"] = answer == "on"
    if not state["context"]["enabled"]:
        update_channel_settings(channel["channel_id"], {"reactions.enabled": False})
        await message.reply_text("Auto reactions disabled.")
        conversation_manager.stop(user_id)
        return
    await message.reply_text("Scope? `all`, `media_only`, or `admin_posts_only`.")
    conversation_manager.set_next(user_id, _handle_reaction_scope)


async def _handle_reaction_scope(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    answer = (message.text or "").strip().lower()
    if answer not in {"all", "media_only", "admin_posts_only"}:
        await message.reply_text("Choose all, media_only, or admin_posts_only.")
        return
    state["context"]["scope"] = answer
    await message.reply_text("Send emojis separated by space (e.g. 🔥 👍 💎).")
    conversation_manager.set_next(user_id, _handle_reaction_emojis)


async def _handle_reaction_emojis(client: Client, message: Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    emojis = [token for token in (message.text or "").split() if token]
    if not emojis:
        await message.reply_text("Please send at least one emoji.")
        return
    channel = state["context"]["channel"]
    update = {
        "reactions": {
            "enabled": True,
            "scope": state["context"]["scope"],
            "emojis": emojis,
        }
    }
    update_channel_settings(channel["channel_id"], update)
    await message.reply_text("Auto reactions updated.")
    conversation_manager.stop(user_id)


async def cmd_status(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    channels_docs = list_channels(user_id)
    if not channels_docs:
        await message.reply_text("No channels configured.")
        return
    await message.reply_text(
        "Send the channel number or ID to view status:\n" +
        "\n".join(
            f"{idx}. {c['title']} ({c.get('channel_username') or c['channel_id']})"
            for idx, c in enumerate(channels_docs, start=1)
        )
    )
    conversation_manager.start(
        user_id,
        _handle_status_selection,
        {"channels": channels_docs},
    )


async def _handle_status_selection(client: Client, message: Message, state: Dict[str, Any]) -> None:
    selection = _parse_channel_selection(message.text or "", state["context"]["channels"])
    if not selection:
        await message.reply_text("Invalid selection.")
        return
    if not await _ensure_access_or_notify(client, message, selection):
        return
    await show_status_summary(message, selection)
    conversation_manager.stop(message.from_user.id)


async def show_status_summary(message: Message, channel: Dict[str, Any]) -> None:
    settings = get_channel_settings(channel["channel_id"]) or {}
    duplicates = settings.get("duplicates", {})
    replies = settings.get("replies", {})
    caption = settings.get("caption", {})
    reactions = settings.get("reactions", {})
    text = (
        f"Channel: **{channel['title']}** ({channel.get('channel_username') or channel['channel_id']})\n"
        f"Duplicates: {'ON' if duplicates.get('enabled') else 'OFF'} (criteria: {', '.join(duplicates.get('criteria', []))})\n"
        f"Replies: {'ON' if replies.get('enabled') else 'OFF'} (mode: {replies.get('mode')})\n"
        f"Caption: {'ON' if caption.get('enabled') else 'OFF'} (apply_to: {', '.join(caption.get('apply_to', []))})\n"
        f"Reactions: {'ON' if reactions.get('enabled') else 'OFF'} (scope: {reactions.get('scope')})"
    )
    await message.reply_text(text)


async def conversation_router(client: Client, message: Message) -> None:
    await conversation_manager.process(client, message)


def register(app: Client) -> None:
    app.add_handler(MessageHandler(cmd_start, filters.private & filters.command("start")))
    app.add_handler(MessageHandler(cmd_help, filters.private & filters.command("help")))
    app.add_handler(MessageHandler(cmd_addchannel, filters.private & filters.command("addchannel")))
    app.add_handler(MessageHandler(cmd_listchannels, filters.private & filters.command("listchannels")))
    app.add_handler(MessageHandler(cmd_removechannel, filters.private & filters.command("removechannel")))
    app.add_handler(MessageHandler(cmd_settings, filters.private & filters.command("settings")))
    app.add_handler(MessageHandler(cmd_dup_settings, filters.private & filters.command("dup_settings")))
    app.add_handler(MessageHandler(cmd_reply_settings, filters.private & filters.command("reply_settings")))
    app.add_handler(MessageHandler(cmd_caption_settings, filters.private & filters.command("caption_settings")))
    app.add_handler(MessageHandler(cmd_reaction_settings, filters.private & filters.command("reaction_settings")))
    app.add_handler(MessageHandler(cmd_status, filters.private & filters.command("status")))
    app.add_handler(
        MessageHandler(
            conversation_router,
            filters.private & filters.text & ~filters.command(),
        ),
        group=1,
    )
