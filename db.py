"""MongoDB helper utilities for the channel management bot."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ReturnDocument

from config import MONGO_DB_NAME, MONGO_URI

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users = db["users"]
channels = db["channels"]
channel_settings = db["channel_settings"]
action_logs = db["action_logs"]

DEFAULT_CHANNEL_SETTINGS: Dict[str, Any] = {
    "duplicates": {
        "enabled": False,
        "criteria": ["text"],
        "scope": "channel",
        "window_type": "messages",
        "window_value": 20,
        "strategy": "delete_new",
    },
    "replies": {
        "enabled": False,
        "mode": "keep_latest",
        "time_limit_minutes": 60,
        "max_replies": 3,
        "ignore_admin_replies": True,
    },
    "caption": {
        "enabled": False,
        "apply_to": ["media"],
        "on_existing_caption": "append",
        "template": "",
    },
    "reactions": {
        "enabled": False,
        "emojis": ["👍"],
        "scope": "all",
    },
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow(),
}


def ensure_indexes() -> None:
    """Create the indexes required for the collections."""
    channels.create_index("owner_user_id")
    channel_settings.create_index("channel_id", unique=True)
    action_logs.create_index("created_at")


def get_or_create_user(user_id: int, first_name: str | None = None, username: str | None = None) -> Dict[str, Any]:
    """Return an existing user profile or create a new one."""
    update: Dict[str, Any] = {
        "$setOnInsert": {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
        },
        "$set": {
            "first_name": first_name,
            "username": username,
            "updated_at": datetime.utcnow(),
        },
    }
    return users.find_one_and_update(
        {"user_id": user_id},
        update,
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )


def add_channel(user_id: int, channel_id: int, channel_username: str | None, title: str) -> Dict[str, Any]:
    """Register a channel under the given owner."""
    channel_doc = channels.find_one_and_update(
        {"channel_id": channel_id},
        {
            "$set": {
                "owner_user_id": user_id,
                "channel_username": channel_username,
                "title": title,
                "active": True,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    ensure_channel_settings(channel_id, user_id)
    return channel_doc


def ensure_channel_settings(channel_id: int, owner_user_id: int) -> Dict[str, Any]:
    """Ensure the channel has a settings document."""
    settings = channel_settings.find_one({"channel_id": channel_id})
    if settings:
        return settings
    new_settings = deepcopy(DEFAULT_CHANNEL_SETTINGS)
    new_settings.update(
        {
            "channel_id": channel_id,
            "owner_user_id": owner_user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )
    channel_settings.insert_one(new_settings)
    return new_settings


def list_channels(user_id: int) -> List[Dict[str, Any]]:
    """List all channels owned by a user."""
    return list(channels.find({"owner_user_id": user_id, "active": True}))


def get_channel(channel_id: int) -> Optional[Dict[str, Any]]:
    """Return the channel document if managed."""
    return channels.find_one({"channel_id": channel_id, "active": True})


def remove_channel(user_id: int, channel_id: int) -> bool:
    """Remove a channel from management."""
    result = channels.update_one(
        {"channel_id": channel_id, "owner_user_id": user_id},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}},
    )
    if result.modified_count:
        channel_settings.delete_one({"channel_id": channel_id})
        return True
    return False


def get_channel_settings(channel_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the channel settings."""
    return channel_settings.find_one({"channel_id": channel_id})


def update_channel_settings(channel_id: int, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Update the settings for a channel."""
    settings_dict["updated_at"] = datetime.utcnow()
    return channel_settings.find_one_and_update(
        {"channel_id": channel_id},
        {"$set": settings_dict},
        return_document=ReturnDocument.AFTER,
    )


def log_action(channel_id: int, owner_user_id: int, action: str, meta: Dict[str, Any] | None = None) -> None:
    """Persist an action log entry."""
    action_logs.insert_one(
        {
            "channel_id": channel_id,
            "owner_user_id": owner_user_id,
            "action": action,
            "meta": meta or {},
            "created_at": datetime.utcnow(),
        }
    )
