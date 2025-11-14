from __future__ import annotations

from typing import Iterable, List, Set

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from config_store import ForwardTask

from . import callbacks
from .text import (
    BTN_ABOUT,
    BTN_ADD_TASK,
    BTN_BACK,
    BTN_BACK_TASK,
    BTN_BOT_MODE,
    BTN_CAPTION_FORMATS,
    BTN_CAPTION_VARS,
    BTN_HELP,
    BTN_HOME,
    BTN_SHOW_TASKS,
    BTN_USER_GUIDE,
    BTN_USER_MODE,
    MEDIA_FILTER_OPTIONS,
    VALID_MEDIA_TYPES,
)


CANCEL_TEXT = "❌ 𝙲𝚊𝚗𝚌𝚎𝚕 ❌"


def create_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(CANCEL_TEXT)]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def remove_cancel_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


MEDIA_ICONS = {
    "text": "🏷️",
    "document": "🗂️",
    "video": "📼",
    "photo": "🖼️",
    "audio": "🎵",
    "voice": "🎙️",
    "sticker": "🦋",
    "animation": "🎭",
}


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_ADD_TASK, callback_data=callbacks.CALLBACK_MENU_ADD_TASK
                ),
                InlineKeyboardButton(
                    BTN_SHOW_TASKS, callback_data=callbacks.CALLBACK_MENU_SHOW_TASKS
                ),
            ],
            [
                InlineKeyboardButton(
                    BTN_HELP, callback_data=callbacks.CALLBACK_MENU_HELP
                ),
                InlineKeyboardButton(
                    BTN_ABOUT, callback_data=callbacks.CALLBACK_MENU_ABOUT
                ),
            ],
        ]
    )


def forward_mode_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_BOT_MODE, callback_data=callbacks.CALLBACK_ADD_MODE_BOT
                ),
                InlineKeyboardButton(
                    BTN_USER_MODE,
                    callback_data=callbacks.CALLBACK_ADD_MODE_USER,
                ),
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK, callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ],
        ]
    )


def add_task_target_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add Channel",
                    callback_data=callbacks.CALLBACK_ADD_TARGET_PROMPT,
                )
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK,
                    callback_data=callbacks.CALLBACK_ADD_BACK_TO_MODE,
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ],
        ]
    )


def add_task_target_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    CANCEL_TEXT,
                    callback_data=callbacks.CALLBACK_ADD_PROMPT_CANCEL,
                )
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK,
                    callback_data=callbacks.CALLBACK_ADD_TARGET_MENU,
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ]
        ]
    )


def add_task_source_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📥 Use Source Channel/Group",
                    callback_data=callbacks.CALLBACK_ADD_SOURCE_PROMPT,
                )
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK,
                    callback_data=callbacks.CALLBACK_ADD_TARGET_MENU,
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ],
        ]
    )


def add_task_source_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    CANCEL_TEXT,
                    callback_data=callbacks.CALLBACK_ADD_PROMPT_CANCEL,
                )
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK,
                    callback_data=callbacks.CALLBACK_ADD_SOURCE_MENU,
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ]
        ]
    )


def add_task_prompt_cancel_bottom_bar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    CANCEL_TEXT,
                    callback_data=callbacks.CALLBACK_ADD_PROMPT_CANCEL,
                )
            ]
        ]
    )


def add_task_prompt_source_bottom_bar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ 𝙰𝚍𝚍 𝚂𝚘𝚞𝚛𝚌𝚎",
                    callback_data=callbacks.CALLBACK_ADD_SOURCE_PROMPT,
                )
            ]
        ]
    )


def task_actions_keyboard(task: ForwardTask) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✏️ Caption",
                    callback_data=f"{callbacks.CALLBACK_TASK_SET_CAPTION}:{task.task_id}",
                ),
                InlineKeyboardButton(
                    "♻️ Duplicates",
                    callback_data=f"{callbacks.CALLBACK_TASK_TOGGLE_DUPLICATES}:{task.task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📦 Size",
                    callback_data=f"{callbacks.CALLBACK_TASK_SET_SIZE}:{task.task_id}",
                ),
                InlineKeyboardButton(
                    "🎚 Filter",
                    callback_data=f"{callbacks.CALLBACK_TASK_SET_FILTERS}:{task.task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧹 Links",
                    callback_data=f"{callbacks.CALLBACK_TASK_TOGGLE_REMOVE_LINKS}:{task.task_id}",
                ),
                InlineKeyboardButton(
                    "🗑️ Remove",
                    callback_data=f"{callbacks.CALLBACK_TASK_REMOVE}:{task.task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK,
                    callback_data=callbacks.CALLBACK_MENU_SHOW_TASKS,
                ),
            ],
        ]
    )


def back_to_menu_keyboard(
    back_callback: str = callbacks.CALLBACK_BACK_TO_MENU,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_BACK, callback_data=back_callback
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ]
        ]
    )


def _truncate_label(text: str, limit: int = 28) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def tasks_overview_keyboard(tasks: Iterable[ForwardTask]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for task in tasks:
        destination = task.target_name or str(task.target_id)
        rows.append(
            [
                InlineKeyboardButton(
                    f"#{task.task_id} • {_truncate_label(destination)}",
                    callback_data=f"{callbacks.CALLBACK_TASK_OPEN}:{task.task_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                BTN_ADD_TASK, callback_data=callbacks.CALLBACK_MENU_ADD_TASK
            ),
            InlineKeyboardButton(
                "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def caption_prompt_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_CAPTION_VARS,
                    callback_data=callbacks.CALLBACK_CAPTION_VARIABLES,
                ),
                InlineKeyboardButton(
                    BTN_CAPTION_FORMATS,
                    callback_data=callbacks.CALLBACK_CAPTION_MARKDOWN,
                ),
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK_TASK,
                    callback_data=f"{callbacks.CALLBACK_TASK_OPEN}:{task_id}",
                ),
            ],
        ]
    )


def no_tasks_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_ADD_TASK, callback_data=callbacks.CALLBACK_MENU_ADD_TASK
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ],
        ]
    )


def size_settings_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔼 Max",
                    callback_data=f"{callbacks.CALLBACK_SIZE_SET_MAX}:{task_id}",
                ),
                InlineKeyboardButton(
                    "🔽 Min",
                    callback_data=f"{callbacks.CALLBACK_SIZE_SET_MIN}:{task_id}",
                ),
                InlineKeyboardButton(
                    "♻️ Reset",
                    callback_data=f"{callbacks.CALLBACK_SIZE_RESET}:{task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK,
                    callback_data=f"{callbacks.CALLBACK_SIZE_BACK}:{task_id}",
                ),
                InlineKeyboardButton(
                    "🏠 Home", callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ],
        ]
    )


def help_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_USER_GUIDE,
                    callback_data=callbacks.CALLBACK_HELP_HOW_TO_USE,
                ),
            ],
            [
                InlineKeyboardButton(
                    BTN_BACK, callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
                InlineKeyboardButton(
                    BTN_HOME, callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ],
        ]
    )


def help_how_to_use_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    BTN_BACK, callback_data=callbacks.CALLBACK_HELP_BACK
                ),
                InlineKeyboardButton(
                    BTN_HOME, callback_data=callbacks.CALLBACK_BACK_TO_MENU
                ),
            ]
        ]
    )


def media_label(media_type: str) -> str:
    return VALID_MEDIA_TYPES.get(media_type, media_type.replace("_", " ").title())


def normalise_media_types(values: Iterable[str]) -> List[str]:
    clean: Set[str] = set()
    for value in values:
        value = value.strip().lower()
        if not value:
            continue
        if value not in VALID_MEDIA_TYPES:
            continue
        if value == "all":
            return ["all"]
        clean.add(value)
    return sorted(clean)


def selected_media_from_task(task: ForwardTask) -> Set[str]:
    if not task.media_types:
        return set()
    if "all" in task.media_types:
        return set(MEDIA_FILTER_OPTIONS)
    return {m for m in task.media_types if m in MEDIA_FILTER_OPTIONS}


def describe_selected_media(selected: Iterable[str]) -> str:
    chosen = [media_label(media) for media in MEDIA_FILTER_OPTIONS if media in selected]
    if not chosen:
        return "<b>None (forwarding paused)</b>"
    if len(chosen) == len(MEDIA_FILTER_OPTIONS):
        return f"<b>{media_label('all')}</b>"
    return ", ".join(f"<b>{label}</b>" for label in chosen)


def render_filter_prompt(selected: Set[str]) -> str:
    return (
        "<b>Toggle the media types you want to forward.</b>\n"
        "<b>All options start enabled, tap any button below to disable ones you don't need.</b>\n\n"
        f"<b>Currently enabled:</b> {describe_selected_media(selected)}"
    )


def build_filter_keyboard(task_id: int, selected: Set[str]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for key in MEDIA_FILTER_OPTIONS:
        label = f"{MEDIA_ICONS.get(key, '•')} {media_label(key)}"
        status = "✅" if key in selected else "❌"
        rows.append(
            [
                InlineKeyboardButton(label, callback_data="noop"),
                InlineKeyboardButton(
                    status,
                    callback_data=f"{callbacks.CALLBACK_FILTER_TOGGLE}:{task_id}:{key}",
                ),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                BTN_BACK,
                callback_data=f"{callbacks.CALLBACK_FILTER_CANCEL}:{task_id}",
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)
