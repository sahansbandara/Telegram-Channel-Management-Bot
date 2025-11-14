from __future__ import annotations

from contextlib import suppress
from dataclasses import replace
from typing import Dict, Optional, Set

from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from config_store import DEFAULT_MAX_MEDIA_SIZE, ForwardTask

from . import callbacks
from .config import APP, STORE, logger
from .state import ChatAccessInfo, PENDING_ACTIONS
from .tasks import (
    clear_duplicate_history,
    format_size_value,
    parse_size_limits,
    render_task,
    send_forward,
)
from .text import (
    ABOUT_TXT,
    ADD_TASK_SOURCE_ACCESS_NOTE_BOT,
    ADD_TASK_SOURCE_ACCESS_NOTE_USER,
    ADD_TASK_SOURCE_MENU,
    ADD_TASK_SOURCE_PROMPT,
    ADD_TASK_TARGET_ACCESS_NOTE_BOT,
    ADD_TASK_TARGET_ACCESS_NOTE_USER,
    ADD_TASK_TARGET_MENU_EMPTY,
    ADD_TASK_TARGET_MENU_SELECTED,
    ADD_TASK_TARGET_PROMPT,
    CAPTION_INSTRUCTIONS,
    CAPTION_MARKDOWN_HELP,
    CAPTION_VARIABLES_HELP,
    CUSTOMIZE_PANEL_TEXT,
    FILE_SIZE_MSG,
    FORWARD_MODE_TXT,
    GUIDE_TXT,
    HOWTO_TXT,
    MEDIA_FILTER_OPTIONS,
    NO_TASKS_MSG,
    START_PANEL_IMAGE,
    START_TXT,
    VALID_MEDIA_TYPES,
)
from .ui import (
    CANCEL_TEXT,
    add_task_prompt_cancel_bottom_bar,
    add_task_prompt_source_bottom_bar,
    add_task_source_menu_keyboard,
    add_task_source_prompt_keyboard,
    add_task_target_menu_keyboard,
    add_task_target_prompt_keyboard,
    back_to_menu_keyboard,
    build_filter_keyboard,
    caption_prompt_keyboard,
    create_cancel_keyboard,
    forward_mode_menu,
    help_how_to_use_keyboard,
    help_menu_keyboard,
    main_menu_keyboard,
    media_label,
    no_tasks_keyboard,
    normalise_media_types,
    remove_cancel_keyboard,
    render_filter_prompt,
    selected_media_from_task,
    size_settings_keyboard,
    task_actions_keyboard,
    tasks_overview_keyboard,
)


def reset_action(user_id: int) -> None:
    PENDING_ACTIONS.pop(user_id, None)


BOTTOM_BAR_PLACEHOLDER = "\u2063"


async def clear_add_wizard_cancel_keyboard(
    client: Client, state: Dict[str, object]
) -> Optional[int]:
    chat_id = state.get("chat_id")
    message_id = state.pop("cancel_keyboard_message_id", None)
    if not chat_id or not message_id:
        return None
    with suppress(RPCError, ValueError):
        await client.delete_messages(int(chat_id), int(message_id))
    return int(chat_id)


async def ensure_add_wizard_cancel_keyboard_removed(
    client: Client, state: Dict[str, object]
) -> None:
    chat_id = await clear_add_wizard_cancel_keyboard(client, state)
    if not chat_id:
        return
    try:
        message = await client.send_message(
            chat_id,
            BOTTOM_BAR_PLACEHOLDER,
            reply_markup=remove_cancel_keyboard(),
            disable_notification=True,
        )
    except RPCError:
        return
    with suppress(RPCError, ValueError):
        await client.delete_messages(chat_id, message.id)


async def clear_add_wizard_bottom_bar(client: Client, state: Dict[str, object]) -> None:
    chat_id = state.get("chat_id")
    bar_id = state.pop("bottom_bar_message_id", None)
    if not chat_id or not bar_id:
        return
    with suppress(RPCError, ValueError):
        await client.delete_messages(int(chat_id), int(bar_id))


async def set_add_wizard_bottom_bar(
    client: Client, state: Dict[str, object], keyboard: InlineKeyboardMarkup
) -> None:
    chat_id = state.get("chat_id")
    if not chat_id:
        return
    await clear_add_wizard_bottom_bar(client, state)
    message = await client.send_message(
        int(chat_id),
        BOTTOM_BAR_PLACEHOLDER,
        reply_markup=keyboard,
        disable_notification=True,
    )
    state["bottom_bar_message_id"] = message.id


async def set_add_wizard_cancel_keyboard(
    client: Client, state: Dict[str, object]
) -> None:
    chat_id = state.get("chat_id")
    if not chat_id:
        return
    await clear_add_wizard_cancel_keyboard(client, state)
    message = await client.send_message(
        int(chat_id),
        BOTTOM_BAR_PLACEHOLDER,
        reply_markup=create_cancel_keyboard(),
        disable_notification=True,
    )
    state["cancel_keyboard_message_id"] = message.id


async def reset_action_with_cleanup(client: Client, user_id: int) -> None:
    state = get_add_wizard_state(user_id)
    if state:
        await ensure_add_wizard_cancel_keyboard_removed(client, state)
        await clear_add_wizard_bottom_bar(client, state)
    reset_action(user_id)


async def build_start_caption(
    client: Client, user_first_name: Optional[str]
) -> str:
    bot_user = await client.get_me()
    first_name = user_first_name or "there"
    bot_username = bot_user.username or str(bot_user.id)
    display_name = bot_user.first_name or bot_user.last_name or bot_username
    if bot_user.first_name and bot_user.last_name:
        display_name = f"{bot_user.first_name} {bot_user.last_name}"
    return START_TXT.format(first_name, bot_username, display_name)


def get_caption_state(user_id: int) -> Optional[Dict[str, object]]:
    state = PENDING_ACTIONS.get(user_id)
    if not state or state.get("action") != "setcaption":
        return None
    return state


def get_size_state(user_id: int) -> Optional[Dict[str, object]]:
    state = PENDING_ACTIONS.get(user_id)
    if not state or state.get("action") != "setsize":
        return None
    return state


def build_caption_prompt(section: Optional[str] = None) -> str:
    text = CAPTION_INSTRUCTIONS
    if section == "variables":
        text += "\n\n" + CAPTION_VARIABLES_HELP
    elif section == "markdown":
        text += "\n\n" + CAPTION_MARKDOWN_HELP
    return text


def get_wizard_mode(state: Dict[str, object]) -> str:
    return "user" if state.get("mode") == "user" else "bot"


def render_target_menu(state: Dict[str, object]) -> str:
    data = state.setdefault("data", {})  # type: ignore[assignment]
    target = data.get("target_info")
    if isinstance(target, ChatAccessInfo):
        return ADD_TASK_TARGET_MENU_SELECTED.format(
            title=target.display_name, chat_id=target.chat_id
        )
    return ADD_TASK_TARGET_MENU_EMPTY


def render_target_prompt(state: Dict[str, object]) -> str:
    mode = get_wizard_mode(state)
    access_note = (
        ADD_TASK_TARGET_ACCESS_NOTE_USER
        if mode == "user"
        else ADD_TASK_TARGET_ACCESS_NOTE_BOT
    )
    return ADD_TASK_TARGET_PROMPT.format(access_note=access_note)


def render_source_menu(state: Dict[str, object]) -> str:
    data = state.setdefault("data", {})  # type: ignore[assignment]
    target = data.get("target_info")
    if isinstance(target, ChatAccessInfo):
        return ADD_TASK_SOURCE_MENU.format(
            title=target.display_name, chat_id=target.chat_id
        )
    return ADD_TASK_TARGET_MENU_EMPTY


def render_source_prompt(state: Dict[str, object]) -> str:
    mode = get_wizard_mode(state)
    access_note = (
        ADD_TASK_SOURCE_ACCESS_NOTE_USER
        if mode == "user"
        else ADD_TASK_SOURCE_ACCESS_NOTE_BOT
    )
    return ADD_TASK_SOURCE_PROMPT.format(access_note=access_note)


def render_size_settings(task: ForwardTask) -> str:
    effective_max = (
        task.max_media_size if task.max_media_size is not None else DEFAULT_MAX_MEDIA_SIZE
    )
    max_display = (
        "Any size" if task.max_media_size is None else format_size_value(effective_max)
    )
    min_display = (
        "0 MB" if task.min_media_size is None else format_size_value(task.min_media_size)
    )

    if task.min_media_size is None and task.max_media_size is None:
        skip_notice = "⚠️ Files of any size will be forwarded."
    elif task.min_media_size is None:
        skip_notice = (
            f"⚠️ Files larger than <b>{max_display}</b> will be skipped automatically."
        )
    elif task.max_media_size is None:
        skip_notice = (
            f"⚠️ Files smaller than <b>{min_display}</b> will be skipped automatically."
        )
    else:
        skip_notice = (
            f"⚠️ Files smaller than <b>{min_display}</b> or larger than <b>{max_display}</b> "
            "will be skipped automatically."
        )

    return FILE_SIZE_MSG.format(
        max_size=max_display,
        min_size=min_display,
        skip_notice=skip_notice,
    )


async def edit_message_content(
    client: Client,
    chat_id: int,
    message_id: int,
    text: str,
    *,
    reply_markup=None,
    parse_mode: Optional[ParseMode] = ParseMode.HTML,
    disable_web_page_preview: bool = True,
) -> Message:
    try:
        return await client.edit_message_text(
            chat_id,
            message_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            parse_mode=parse_mode,
        )
    except RPCError as err:
        logger.debug("Unable to edit message text: %s", err)

    try:
        return await client.edit_message_caption(
            chat_id,
            message_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except RPCError as err:
        logger.debug("Unable to edit message caption: %s", err)

    return await client.send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
        disable_web_page_preview=disable_web_page_preview,
        parse_mode=parse_mode,
    )


async def update_size_panel(
    client: Client,
    state: Dict[str, object],
    task: ForwardTask,
    *,
    note: Optional[str] = None,
) -> None:
    chat_id = state.get("chat_id")
    message_id = state.get("summary_message_id")
    if not chat_id or not message_id:
        return

    text = render_size_settings(task)
    if note:
        text = f"{note}\n\n{text}"

    message = await edit_message_content(
        client,
        int(chat_id),
        int(message_id),
        text,
        reply_markup=size_settings_keyboard(task.task_id),
        parse_mode=ParseMode.HTML,
    )
    state["chat_id"] = message.chat.id
    state["summary_message_id"] = message.id


async def safe_edit_message(
    client: Client,
    query: CallbackQuery,
    text: str,
    *,
    reply_markup=None,
    disable_web_page_preview: bool = True,
    parse_mode: Optional[ParseMode] = ParseMode.HTML,
) -> Message:
    return await edit_message_content(
        client,
        query.message.chat.id,
        query.message.id,
        text,
        reply_markup=reply_markup,
        disable_web_page_preview=disable_web_page_preview,
        parse_mode=parse_mode,
    )


async def start_handler(client: Client, message: Message) -> None:
    user_first_name = message.from_user.first_name if message.from_user else None
    await message.reply_photo(
        START_PANEL_IMAGE,
        caption=await build_start_caption(client, user_first_name),
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def help_handler(client: Client, message: Message) -> None:
    await message.reply(
        GUIDE_TXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=help_menu_keyboard(),
    )


async def guide_handler(client: Client, message: Message) -> None:
    await message.reply(
        HOWTO_TXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=help_how_to_use_keyboard(),
    )


async def cancel_handler(client: Client, message: Message) -> None:
    await reset_action_with_cleanup(client, message.from_user.id)
    await message.reply("Current action cancelled.")


def get_add_wizard_state(user_id: int) -> Optional[Dict[str, object]]:
    state = PENDING_ACTIONS.get(user_id)
    if not state or state.get("action") != "add_wizard":
        return None
    return state


async def handle_add_task_button(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    await reset_action_with_cleanup(client, user_id)
    state: Dict[str, object] = {
        "action": "add_wizard",
        "step": "mode",
        "chat_id": query.message.chat.id,
        "data": {},
    }
    PENDING_ACTIONS[user_id] = state
    message = await safe_edit_message(
        client,
        query,
        FORWARD_MODE_TXT,
        reply_markup=forward_mode_menu(),
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await query.answer()


async def handle_show_tasks_button(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    await reset_action_with_cleanup(client, user_id)
    tasks = STORE.list_tasks(user_id)
    if not tasks:
        await safe_edit_message(
            client,
            query,
            NO_TASKS_MSG,
            reply_markup=no_tasks_keyboard(),
        )
        await query.answer()
        return
    else:
        text = (
            "📋 <b>Your forwarding tasks</b>\n\n"
            "Tap a task below to view details or customize forwarding."
        )
        markup = tasks_overview_keyboard(tasks)
    await safe_edit_message(client, query, text, reply_markup=markup)
    await query.answer()


async def handle_customize_button(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    await reset_action_with_cleanup(client, user_id)
    tasks = STORE.list_tasks(user_id)
    markup = tasks_overview_keyboard(tasks) if tasks else main_menu_keyboard()
    await safe_edit_message(
        client,
        query,
        CUSTOMIZE_PANEL_TEXT,
        reply_markup=markup,
    )
    await query.answer()


async def handle_help_button(client: Client, query: CallbackQuery) -> None:
    await reset_action_with_cleanup(client, query.from_user.id)
    await safe_edit_message(
        client,
        query,
        GUIDE_TXT,
        reply_markup=help_menu_keyboard(),
        disable_web_page_preview=True,
    )
    await query.answer()


async def handle_about_button(client: Client, query: CallbackQuery) -> None:
    await reset_action_with_cleanup(client, query.from_user.id)
    await safe_edit_message(
        client,
        query,
        ABOUT_TXT,
        reply_markup=back_to_menu_keyboard(),
    )
    await query.answer()


async def handle_add_mode_selection(
    client: Client, query: CallbackQuery, mode: str
) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Start task creation first.", show_alert=True)
        return

    state["mode"] = mode
    state["step"] = "target_menu"
    data: Dict[str, object] = state.setdefault("data", {})  # type: ignore[assignment]
    data.pop("target_info", None)
    data.pop("source_info", None)

    message = await safe_edit_message(
        client,
        query,
        render_target_menu(state),
        reply_markup=add_task_target_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await query.answer("Mode selected")


async def handle_help_how_to_use(client: Client, query: CallbackQuery) -> None:
    await safe_edit_message(
        client,
        query,
        HOWTO_TXT,
        reply_markup=help_how_to_use_keyboard(),
        disable_web_page_preview=True,
    )
    await query.answer()


async def handle_help_back(client: Client, query: CallbackQuery) -> None:
    await safe_edit_message(
        client,
        query,
        GUIDE_TXT,
        reply_markup=help_menu_keyboard(),
        disable_web_page_preview=True,
    )
    await query.answer()


async def handle_add_show_target_menu(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Start task creation first.", show_alert=True)
        return

    state["step"] = "target_menu"
    await ensure_add_wizard_cancel_keyboard_removed(client, state)
    await clear_add_wizard_bottom_bar(client, state)
    message = await safe_edit_message(
        client,
        query,
        render_target_menu(state),
        reply_markup=add_task_target_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await query.answer()


async def handle_add_back_to_mode(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Start task creation first.", show_alert=True)
        return

    state["step"] = "mode"
    await ensure_add_wizard_cancel_keyboard_removed(client, state)
    await clear_add_wizard_bottom_bar(client, state)
    message = await safe_edit_message(
        client,
        query,
        FORWARD_MODE_TXT,
        reply_markup=forward_mode_menu(),
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await query.answer()


async def handle_add_target_prompt(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Start task creation first.", show_alert=True)
        return

    state["step"] = "target"
    await clear_add_wizard_cancel_keyboard(client, state)
    message = await safe_edit_message(
        client,
        query,
        render_target_prompt(state),
        reply_markup=add_task_target_prompt_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await set_add_wizard_bottom_bar(
        client, state, add_task_prompt_cancel_bottom_bar()
    )
    await set_add_wizard_cancel_keyboard(client, state)
    await query.answer("Send the destination chat")


async def handle_add_source_menu(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Start task creation first.", show_alert=True)
        return

    data = state.get("data", {})
    if not isinstance(data, dict) or "target_info" not in data:
        await query.answer("Choose a target chat first.", show_alert=True)
        return

    state["step"] = "source_menu"
    await ensure_add_wizard_cancel_keyboard_removed(client, state)
    await clear_add_wizard_bottom_bar(client, state)
    message = await safe_edit_message(
        client,
        query,
        render_source_menu(state),
        reply_markup=add_task_source_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await query.answer()


async def handle_add_source_prompt(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Start task creation first.", show_alert=True)
        return

    data = state.get("data", {})
    if not isinstance(data, dict) or "target_info" not in data:
        await query.answer("Choose a target chat first.", show_alert=True)
        return

    state["step"] = "source"
    await clear_add_wizard_cancel_keyboard(client, state)
    message = await safe_edit_message(
        client,
        query,
        render_source_prompt(state),
        reply_markup=add_task_source_prompt_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    state["chat_id"] = message.chat.id
    state["menu_message_id"] = message.id
    await set_add_wizard_bottom_bar(
        client, state, add_task_prompt_cancel_bottom_bar()
    )
    await set_add_wizard_cancel_keyboard(client, state)
    await query.answer("Send the source chat")


async def handle_add_prompt_cancel(client: Client, query: CallbackQuery) -> None:
    user_id = query.from_user.id
    state = get_add_wizard_state(user_id)
    if not state:
        await query.answer("Nothing to cancel.", show_alert=True)
        return

    step = state.get("step")
    cleanup_chat_id = await clear_add_wizard_cancel_keyboard(client, state)
    if step == "target":
        state["step"] = "target_menu"
        await clear_add_wizard_bottom_bar(client, state)
        message = await safe_edit_message(
            client,
            query,
            render_target_menu(state),
            reply_markup=add_task_target_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        state["chat_id"] = message.chat.id
        state["menu_message_id"] = message.id
        if cleanup_chat_id:
            await client.send_message(
                cleanup_chat_id,
                "❌ 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.",
                reply_markup=remove_cancel_keyboard(),
                disable_notification=True,
            )
        await query.answer("Cancelled.")
        return

    if step == "source":
        state["step"] = "source_menu"
        await clear_add_wizard_bottom_bar(client, state)
        message = await safe_edit_message(
            client,
            query,
            render_source_menu(state),
            reply_markup=add_task_source_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        state["chat_id"] = message.chat.id
        state["menu_message_id"] = message.id
        if cleanup_chat_id:
            await client.send_message(
                cleanup_chat_id,
                "❌ 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.",
                reply_markup=remove_cancel_keyboard(),
                disable_notification=True,
            )
        await query.answer("Cancelled.")
        return

    await query.answer("Nothing to cancel.", show_alert=True)


async def fetch_chat(client: Client, identifier: str) -> ChatAccessInfo:
    chat = await client.get_chat(identifier)
    title = chat.title or chat.first_name or chat.username or str(chat.id)
    is_public = bool(getattr(chat, "username", None))
    return ChatAccessInfo(chat.id, title, is_public, chat.type)


async def conclude_add_wizard(
    client: Client, user_id: int, chat_id: int, task: ForwardTask
) -> None:
    await reset_action_with_cleanup(client, user_id)
    await client.send_message(
        chat_id,
        "Forwarding task created successfully!\n\n" + render_task(task),
        reply_markup=task_actions_keyboard(task),
        parse_mode=ParseMode.HTML,
    )


def parse_task_id(data: str, prefix: str) -> Optional[int]:
    if not data.startswith(prefix + ":"):
        return None
    try:
        return int(data.split(":", 1)[1])
    except ValueError:
        return None


def get_filter_editor_state(user_id: int) -> Optional[Dict[str, object]]:
    state = PENDING_ACTIONS.get(user_id)
    if not state or state.get("action") != "filters_ui":
        return None
    return state


async def refresh_filter_editor(
    client: Client, state: Dict[str, object], selected: Set[str]
) -> None:
    task: ForwardTask = state["task"]  # type: ignore[assignment]
    editor_chat_id = state.get("editor_chat_id")
    editor_message_id = state.get("editor_message_id")
    if not editor_chat_id or not editor_message_id:
        return
    await edit_message_content(
        client,
        int(editor_chat_id),
        int(editor_message_id),
        render_filter_prompt(selected),
        reply_markup=build_filter_keyboard(task.task_id, selected),
    )


def persist_filter_selection(state: Dict[str, object], selected: Set[str]) -> ForwardTask:
    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if len(selected) == len(MEDIA_FILTER_OPTIONS):
        media_types = ["all"]
    else:
        media_types = sorted(selected)

    updated = replace(task, media_types=media_types)
    STORE.update_task(updated)
    state["task"] = updated
    return updated


async def handle_filters_button(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    await reset_action_with_cleanup(client, user_id)
    selected = selected_media_from_task(task)
    editor_message = await safe_edit_message(
        client,
        query,
        render_filter_prompt(selected),
        reply_markup=build_filter_keyboard(task.task_id, selected),
    )
    PENDING_ACTIONS[user_id] = {
        "action": "filters_ui",
        "task": task,
        "selected": set(selected),
        "editor_chat_id": editor_message.chat.id,
        "editor_message_id": editor_message.id,
    }
    await query.answer("Tap to toggle media types")


async def handle_filter_toggle(
    client: Client, query: CallbackQuery, task_id: int, media_type: str
) -> None:
    user_id = query.from_user.id
    state = get_filter_editor_state(user_id)
    if not state:
        await query.answer("Open the media filter menu first.", show_alert=True)
        return

    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if task.task_id != task_id:
        await query.answer("This media filter menu is no longer active.", show_alert=True)
        return

    selected: Set[str] = set(state.get("selected", set()))  # type: ignore[arg-type]
    if media_type in selected:
        selected.remove(media_type)
        feedback = f"{media_label(media_type)} off"
    else:
        selected.add(media_type)
        feedback = f"{media_label(media_type)} on"
    state["selected"] = selected
    persist_filter_selection(state, selected)
    await refresh_filter_editor(client, state, selected)
    await query.answer(feedback)


async def handle_filter_select_all(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_filter_editor_state(user_id)
    if not state:
        await query.answer("Open the media filter menu first.", show_alert=True)
        return

    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if task.task_id != task_id:
        await query.answer("This media filter menu is no longer active.", show_alert=True)
        return

    selected = set(MEDIA_FILTER_OPTIONS)
    state["selected"] = selected
    persist_filter_selection(state, selected)
    await refresh_filter_editor(client, state, selected)
    await query.answer("All media enabled")


async def handle_filter_select_none(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_filter_editor_state(user_id)
    if not state:
        await query.answer("Open the media filter menu first.", show_alert=True)
        return

    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if task.task_id != task_id:
        await query.answer("This media filter menu is no longer active.", show_alert=True)
        return

    selected: Set[str] = set()
    state["selected"] = selected
    persist_filter_selection(state, selected)
    await refresh_filter_editor(client, state, selected)
    await query.answer("All media disabled")


async def handle_filter_save(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_filter_editor_state(user_id)
    if not state:
        await query.answer("Open the media filter menu first.", show_alert=True)
        return

    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if task.task_id != task_id:
        await query.answer("This media filter menu is no longer active.", show_alert=True)
        return

    selected: Set[str] = set(state.get("selected", set()))  # type: ignore[arg-type]
    updated = persist_filter_selection(state, selected)

    editor_chat_id = state.get("editor_chat_id")
    editor_message_id = state.get("editor_message_id")

    await reset_action_with_cleanup(client, user_id)

    if editor_chat_id and editor_message_id:
        await edit_message_content(
            client,
            int(editor_chat_id),
            int(editor_message_id),
            render_task(updated),
            reply_markup=task_actions_keyboard(updated),
            parse_mode=ParseMode.HTML,
        )

    await query.answer("Filters saved")


async def handle_filter_cancel(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_filter_editor_state(user_id)
    if not state:
        await query.answer("Nothing to cancel.")
        return

    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if task.task_id != task_id:
        await query.answer("This media filter menu is no longer active.", show_alert=True)
        return

    editor_chat_id = state.get("editor_chat_id")
    editor_message_id = state.get("editor_message_id")
    await reset_action_with_cleanup(client, user_id)
    if editor_chat_id and editor_message_id:
        await edit_message_content(
            client,
            int(editor_chat_id),
            int(editor_message_id),
            render_task(task),
            reply_markup=task_actions_keyboard(task),
            parse_mode=ParseMode.HTML,
        )
    await query.answer("Back to task")


async def handle_open_task(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return
    await reset_action_with_cleanup(client, user_id)
    await safe_edit_message(
        client,
        query,
        render_task(task),
        reply_markup=task_actions_keyboard(task),
    )
    await query.answer()


async def handle_caption_button(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    await reset_action_with_cleanup(client, user_id)
    prompt_message = await safe_edit_message(
        client,
        query,
        build_caption_prompt(),
        reply_markup=caption_prompt_keyboard(task.task_id),
    )
    PENDING_ACTIONS[user_id] = {
        "action": "setcaption",
        "task": task,
        "chat_id": prompt_message.chat.id,
        "summary_message_id": prompt_message.id,
        "section": None,
    }
    await query.answer("Waiting for caption")


async def handle_caption_help_section(
    client: Client, query: CallbackQuery, section: str
) -> None:
    state = get_caption_state(query.from_user.id)
    if not state:
        await query.answer("Caption editor closed.", show_alert=True)
        return

    task: ForwardTask = state["task"]  # type: ignore[assignment]
    prompt_message = await safe_edit_message(
        client,
        query,
        build_caption_prompt(section),
        reply_markup=caption_prompt_keyboard(task.task_id),
    )
    state["chat_id"] = prompt_message.chat.id
    state["summary_message_id"] = prompt_message.id
    state["section"] = section
    await query.answer()


async def handle_size_button(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    await reset_action_with_cleanup(client, user_id)
    prompt_message = await safe_edit_message(
        client,
        query,
        render_size_settings(task),
        reply_markup=size_settings_keyboard(task.task_id),
    )
    PENDING_ACTIONS[user_id] = {
        "action": "setsize",
        "task": task,
        "chat_id": prompt_message.chat.id,
        "summary_message_id": prompt_message.id,
        "mode": None,
    }
    await query.answer("Size settings ready")


async def handle_size_set_max(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_size_state(user_id)
    if not state:
        await query.answer("Open the size menu first.", show_alert=True)
        return

    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    state["task"] = task
    state["mode"] = "max"
    prompt_message = await safe_edit_message(
        client,
        query,
        render_size_settings(task)
        + "\n\nSend the new <b>maximum size</b> in MB (e.g. <code>500</code>). Reply with <code>-</code> to remove the limit.",
        reply_markup=size_settings_keyboard(task.task_id),
    )
    state["chat_id"] = prompt_message.chat.id
    state["summary_message_id"] = prompt_message.id
    await query.answer("Waiting for maximum size")


async def handle_size_set_min(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_size_state(user_id)
    if not state:
        await query.answer("Open the size menu first.", show_alert=True)
        return

    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    state["task"] = task
    state["mode"] = "min"
    prompt_message = await safe_edit_message(
        client,
        query,
        render_size_settings(task)
        + "\n\nSend the new <b>minimum size</b> in MB (e.g. <code>50</code>). Reply with <code>-</code> to remove the limit.",
        reply_markup=size_settings_keyboard(task.task_id),
    )
    state["chat_id"] = prompt_message.chat.id
    state["summary_message_id"] = prompt_message.id
    await query.answer("Waiting for minimum size")


async def handle_size_reset(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_size_state(user_id)
    if not state:
        await query.answer("Open the size menu first.", show_alert=True)
        return

    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    updated = replace(
        task,
        min_media_size=None,
        max_media_size=DEFAULT_MAX_MEDIA_SIZE,
    )
    STORE.update_task(updated)
    state["task"] = updated
    state["mode"] = None
    await update_size_panel(client, state, updated, note="♻️ Size limits reset.")
    await query.answer("Size limits reset")


async def handle_size_back(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    state = get_size_state(user_id)
    task = STORE.get_task(user_id, task_id)
    if not task and state:
        task = state.get("task")  # type: ignore[assignment]
        if isinstance(task, ForwardTask) and task.task_id != task_id:
            task = None

    await reset_action_with_cleanup(client, user_id)

    if not isinstance(task, ForwardTask):
        await handle_show_tasks_button(client, query)
        return

    await safe_edit_message(
        client,
        query,
        render_task(task),
        reply_markup=task_actions_keyboard(task),
    )
    await query.answer()


async def handle_toggle_duplicates(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    updated = replace(task, skip_duplicates=not task.skip_duplicates)
    STORE.update_task(updated)

    await safe_edit_message(
        client,
        query,
        render_task(updated),
        reply_markup=task_actions_keyboard(updated),
    )
    await query.answer("Duplicate filtering toggled")


async def handle_toggle_remove_links(
    client: Client, query: CallbackQuery, task_id: int
) -> None:
    user_id = query.from_user.id
    task = STORE.get_task(user_id, task_id)
    if not task:
        await query.answer("Task not found.", show_alert=True)
        return

    updated = replace(task, remove_links=not task.remove_links)
    STORE.update_task(updated)

    await safe_edit_message(
        client,
        query,
        render_task(updated),
        reply_markup=task_actions_keyboard(updated),
    )
    await query.answer("Link removal toggled")


async def handle_remove_button(client: Client, query: CallbackQuery, task_id: int) -> None:
    user_id = query.from_user.id
    await reset_action_with_cleanup(client, user_id)
    if STORE.remove_task(user_id, task_id):
        clear_duplicate_history(task_id)
        await safe_edit_message(
            client,
            query,
            f"Task {task_id} removed.",
            reply_markup=None,
        )
        await query.answer("Task removed")
    else:
        await query.answer("Task not found.", show_alert=True)


async def handle_back_to_menu(client: Client, query: CallbackQuery) -> None:
    await reset_action_with_cleanup(client, query.from_user.id)
    await safe_edit_message(
        client,
        query,
        await build_start_caption(
            client, query.from_user.first_name if query.from_user else None
        ),
        reply_markup=main_menu_keyboard(),
    )
    await query.answer()


@APP.on_callback_query()
async def callback_router(client: Client, query: CallbackQuery) -> None:
    data = query.data or ""

    if data == "noop":
        await query.answer()
        return

    if data == callbacks.CALLBACK_MENU_ADD_TASK:
        await handle_add_task_button(client, query)
        return
    if data == callbacks.CALLBACK_MENU_CUSTOMIZE:
        await handle_customize_button(client, query)
        return
    if data == callbacks.CALLBACK_MENU_SHOW_TASKS:
        await handle_show_tasks_button(client, query)
        return
    if data == callbacks.CALLBACK_MENU_HELP:
        await handle_help_button(client, query)
        return
    if data == callbacks.CALLBACK_MENU_ABOUT:
        await handle_about_button(client, query)
        return
    if data == callbacks.CALLBACK_ADD_MODE_BOT:
        await handle_add_mode_selection(client, query, "bot")
        return
    if data == callbacks.CALLBACK_ADD_MODE_USER:
        await handle_add_mode_selection(client, query, "user")
        return
    if data == callbacks.CALLBACK_ADD_TARGET_MENU:
        await handle_add_show_target_menu(client, query)
        return
    if data == callbacks.CALLBACK_ADD_BACK_TO_MODE:
        await handle_add_back_to_mode(client, query)
        return
    if data == callbacks.CALLBACK_ADD_TARGET_PROMPT:
        await handle_add_target_prompt(client, query)
        return
    if data == callbacks.CALLBACK_ADD_SOURCE_MENU:
        await handle_add_source_menu(client, query)
        return
    if data == callbacks.CALLBACK_ADD_SOURCE_PROMPT:
        await handle_add_source_prompt(client, query)
        return
    if data == callbacks.CALLBACK_ADD_PROMPT_CANCEL:
        await handle_add_prompt_cancel(client, query)
        return
    if data == callbacks.CALLBACK_BACK_TO_MENU:
        await handle_back_to_menu(client, query)
        return
    if data == callbacks.CALLBACK_HELP_HOW_TO_USE:
        await handle_help_how_to_use(client, query)
        return
    if data == callbacks.CALLBACK_HELP_BACK:
        await handle_help_back(client, query)
        return
    if data == callbacks.CALLBACK_CAPTION_VARIABLES:
        await handle_caption_help_section(client, query, "variables")
        return
    if data == callbacks.CALLBACK_CAPTION_MARKDOWN:
        await handle_caption_help_section(client, query, "markdown")
        return

    toggle_duplicates_task_id = parse_task_id(
        data, callbacks.CALLBACK_TASK_TOGGLE_DUPLICATES
    )
    if toggle_duplicates_task_id is not None:
        await handle_toggle_duplicates(client, query, toggle_duplicates_task_id)
        return

    toggle_links_task_id = parse_task_id(
        data, callbacks.CALLBACK_TASK_TOGGLE_REMOVE_LINKS
    )
    if toggle_links_task_id is not None:
        await handle_toggle_remove_links(client, query, toggle_links_task_id)
        return

    size_task_id = parse_task_id(data, callbacks.CALLBACK_TASK_SET_SIZE)
    if size_task_id is not None:
        await handle_size_button(client, query, size_task_id)
        return

    size_max_task_id = parse_task_id(data, callbacks.CALLBACK_SIZE_SET_MAX)
    if size_max_task_id is not None:
        await handle_size_set_max(client, query, size_max_task_id)
        return

    size_min_task_id = parse_task_id(data, callbacks.CALLBACK_SIZE_SET_MIN)
    if size_min_task_id is not None:
        await handle_size_set_min(client, query, size_min_task_id)
        return

    size_reset_task_id = parse_task_id(data, callbacks.CALLBACK_SIZE_RESET)
    if size_reset_task_id is not None:
        await handle_size_reset(client, query, size_reset_task_id)
        return

    size_back_task_id = parse_task_id(data, callbacks.CALLBACK_SIZE_BACK)
    if size_back_task_id is not None:
        await handle_size_back(client, query, size_back_task_id)
        return

    if data.startswith(callbacks.CALLBACK_FILTER_TOGGLE + ":"):
        parts = data.split(":", 2)
        if len(parts) == 3 and parts[1].isdigit():
            await handle_filter_toggle(client, query, int(parts[1]), parts[2])
        else:
            await query.answer()
        return

    select_all_task_id = parse_task_id(data, callbacks.CALLBACK_FILTER_SELECT_ALL)
    if select_all_task_id is not None:
        await handle_filter_select_all(client, query, select_all_task_id)
        return

    select_none_task_id = parse_task_id(data, callbacks.CALLBACK_FILTER_SELECT_NONE)
    if select_none_task_id is not None:
        await handle_filter_select_none(client, query, select_none_task_id)
        return

    save_filters_task_id = parse_task_id(data, callbacks.CALLBACK_FILTER_SAVE)
    if save_filters_task_id is not None:
        await handle_filter_save(client, query, save_filters_task_id)
        return

    cancel_filters_task_id = parse_task_id(data, callbacks.CALLBACK_FILTER_CANCEL)
    if cancel_filters_task_id is not None:
        await handle_filter_cancel(client, query, cancel_filters_task_id)
        return

    filters_task_id = parse_task_id(data, callbacks.CALLBACK_TASK_SET_FILTERS)
    if filters_task_id is not None:
        await handle_filters_button(client, query, filters_task_id)
        return

    caption_task_id = parse_task_id(data, callbacks.CALLBACK_TASK_SET_CAPTION)
    if caption_task_id is not None:
        await handle_caption_button(client, query, caption_task_id)
        return

    remove_task_id = parse_task_id(data, callbacks.CALLBACK_TASK_REMOVE)
    if remove_task_id is not None:
        await handle_remove_button(client, query, remove_task_id)
        return

    open_task_id = parse_task_id(data, callbacks.CALLBACK_TASK_OPEN)
    if open_task_id is not None:
        await handle_open_task(client, query, open_task_id)
        return

    await query.answer()


@APP.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message) -> None:
    await start_handler(client, message)


@APP.on_message(filters.private & filters.command("help"))
async def help_command(client: Client, message: Message) -> None:
    await help_handler(client, message)


@APP.on_message(filters.private & filters.command("guide"))
async def guide_command(client: Client, message: Message) -> None:
    await guide_handler(client, message)


@APP.on_message(filters.private & filters.command("cancel"))
async def cancel_command(client: Client, message: Message) -> None:
    await cancel_handler(client, message)


@APP.on_message(filters.private & filters.command("addforward"))
async def add_forward_handler(client: Client, message: Message) -> None:
    user_id = message.from_user.id
    PENDING_ACTIONS[user_id] = {"action": "add", "step": 1, "data": {}}
    await message.reply(
        "Step 1/4 – Send the source chat username or numeric ID.\n"
        "Public chats don't require inviting the bot, but private channels or groups must add the bot as an admin or connect a user session so it can read messages."
    )


@APP.on_message(filters.private & filters.command("list"))
async def list_handler(client: Client, message: Message) -> None:
    tasks = STORE.list_tasks(message.from_user.id)
    if not tasks:
        await message.reply("You have not configured any forwarding tasks yet.")
        return

    await message.reply("Here are your forwarding tasks:")
    for task in tasks:
        await message.reply(
            render_task(task),
            reply_markup=task_actions_keyboard(task),
            parse_mode=ParseMode.HTML,
        )


@APP.on_message(filters.private & filters.command("remove"))
async def remove_handler(client: Client, message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("Usage: /remove <task_id>")
        return

    task_id = int(parts[1])
    if STORE.remove_task(message.from_user.id, task_id):
        clear_duplicate_history(task_id)
        await message.reply(f"Task {task_id} removed.")
    else:
        await message.reply("Task not found.")


@APP.on_message(filters.private & filters.command("setfilters"))
async def set_filters_handler(client: Client, message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("Usage: /setfilters <task_id>")
        return

    task_id = int(parts[1])
    task = STORE.get_task(message.from_user.id, task_id)
    if not task:
        await message.reply("Task not found.")
        return

    PENDING_ACTIONS[message.from_user.id] = {
        "action": "setfilters",
        "step": 1,
        "task": task,
    }
    options = ", ".join(sorted(VALID_MEDIA_TYPES.keys()))
    await message.reply(
        "Send the message types to forward separated by commas.\n"
        f"Available options: {options}.\n"
        "Use 'all' to forward everything."
    )


@APP.on_message(filters.private & filters.command("setcaption"))
async def set_caption_handler(client: Client, message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("Usage: /setcaption <task_id>")
        return

    task_id = int(parts[1])
    task = STORE.get_task(message.from_user.id, task_id)
    if not task:
        await message.reply("Task not found.")
        return

    PENDING_ACTIONS[message.from_user.id] = {
        "action": "setcaption",
        "step": 1,
        "task": task,
    }
    await message.reply(
        "Send the caption text to attach to forwarded messages.\n"
        "Send a single dash (-) to remove the custom caption."
    )


@APP.on_message(filters.private & filters.command("setsize"))
async def set_size_handler(client: Client, message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("Usage: /setsize <task_id>")
        return

    task_id = int(parts[1])
    task = STORE.get_task(message.from_user.id, task_id)
    if not task:
        await message.reply("Task not found.")
        return

    sent = await message.reply(
        render_size_settings(task),
        reply_markup=size_settings_keyboard(task.task_id),
        parse_mode=ParseMode.HTML,
    )
    PENDING_ACTIONS[message.from_user.id] = {
        "action": "setsize",
        "task": task,
        "chat_id": sent.chat.id,
        "summary_message_id": sent.id,
        "mode": None,
    }


@APP.on_message(filters.private)
async def private_message_router(client: Client, message: Message) -> None:
    user_id = message.from_user.id
    state = PENDING_ACTIONS.get(user_id)
    if not state:
        return

    action = state.get("action")
    if action == "add":
        await handle_add_forward_steps(client, message, state)
    elif action == "setfilters":
        await handle_filters_command_input(client, message, state)
    elif action == "setcaption":
        await handle_caption_input(client, message, state)
    elif action == "setsize":
        await handle_size_input(client, message, state)
    elif action == "add_wizard":
        await handle_add_wizard_message(client, message, state)


async def handle_add_forward_steps(
    client: Client, message: Message, state: Dict[str, object]
) -> None:
    step = state.get("step")
    data: Dict[str, object] = state.get("data", {})  # type: ignore[assignment]
    if not message.text:
        await message.reply("Please send the chat username or numeric ID as text.")
        return

    identifier = message.text.strip()

    if step == 1:
        try:
            info = await fetch_chat(client, identifier)
        except RPCError as err:
            await message.reply(
                "Could not access that source chat. Confirm the details or add the bot so it can read messages."
            )
            logger.warning("Failed to fetch source chat %s: %s", identifier, err)
            return
        data["source"] = info
        state["step"] = 2
        await message.reply(
            "Step 2/4 – Send the destination chat username or ID."
        )
    elif step == 2:
        try:
            info = await fetch_chat(client, identifier)
        except RPCError as err:
            await message.reply(
                "Could not access that destination. Check the username or invite the bot before continuing."
            )
            logger.warning("Failed to fetch target chat %s: %s", identifier, err)
            return
        data["target"] = info
        state["step"] = 3
        await message.reply(
            "Step 3/4 – Send the media types to forward separated by commas (or 'all')."
        )
    elif step == 3:
        media_types = normalise_media_types(message.text.split(","))
        if not media_types:
            await message.reply("Invalid media types. Try again.")
            return
        data["media_types"] = media_types
        state["step"] = 4
        await message.reply(
            "Step 4/4 – Send a caption to append to forwarded messages or '-' to skip."
        )
    elif step == 4:
        caption = message.text.strip()
        data["caption"] = None if caption == "-" else caption
        source: ChatAccessInfo = data["source"]  # type: ignore[assignment]
        target: ChatAccessInfo = data["target"]  # type: ignore[assignment]
        media_types = data.get("media_types", ["all"])
        task = STORE.add_task(
            message.from_user.id,
            source_id=source.chat_id,
            source_name=source.display_name,
            target_id=target.chat_id,
            target_name=target.display_name,
            media_types=media_types,
            caption=data["caption"],
        )
        await conclude_add_wizard(
            client, message.from_user.id, message.chat.id, task
        )


async def handle_add_wizard_message(
    client: Client, message: Message, state: Dict[str, object]
) -> None:
    step = state.get("step")
    user_id = message.from_user.id

    if step == "mode":
        await message.reply("Use the buttons to choose a forwarding mode first.")
        return

    if step == "target_menu":
        await message.reply("Tap the Add Channel button to choose the destination first.")
        return

    if step == "source_menu":
        await message.reply(
            "Tap the Use Source Channel/Group button before sending the chat details."
        )
        return

    if step not in {"target", "source"}:
        return

    if not message.text:
        await message.reply("Please send the chat username or ID as text.")
        return

    identifier = message.text.strip()
    if identifier == CANCEL_TEXT:
        cleanup_chat_id = await clear_add_wizard_cancel_keyboard(client, state)
        if step == "target":
            state["step"] = "target_menu"
            await clear_add_wizard_bottom_bar(client, state)
            menu_chat_id = state.get("chat_id")
            menu_message_id = state.get("menu_message_id")
            if menu_chat_id and menu_message_id:
                updated = await edit_message_content(
                    client,
                    int(menu_chat_id),
                    int(menu_message_id),
                    render_target_menu(state),
                    reply_markup=add_task_target_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
                state["chat_id"] = updated.chat.id
                state["menu_message_id"] = updated.id
            await message.reply(
                "❌ 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.", reply_markup=remove_cancel_keyboard()
            )
            return
        if step == "source":
            state["step"] = "source_menu"
            await clear_add_wizard_bottom_bar(client, state)
            menu_chat_id = state.get("chat_id")
            menu_message_id = state.get("menu_message_id")
            if menu_chat_id and menu_message_id:
                updated = await edit_message_content(
                    client,
                    int(menu_chat_id),
                    int(menu_message_id),
                    render_source_menu(state),
                    reply_markup=add_task_source_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
                state["chat_id"] = updated.chat.id
                state["menu_message_id"] = updated.id
            await message.reply(
                "❌ 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.", reply_markup=remove_cancel_keyboard()
            )
            return
        if cleanup_chat_id:
            try:
                cleanup_msg = await client.send_message(
                    cleanup_chat_id,
                    BOTTOM_BAR_PLACEHOLDER,
                    reply_markup=remove_cancel_keyboard(),
                    disable_notification=True,
                )
            except RPCError:
                pass
            else:
                with suppress(RPCError, ValueError):
                    await client.delete_messages(cleanup_chat_id, cleanup_msg.id)
        return

    try:
        chat_info = await fetch_chat(client, identifier)
    except RPCError as err:
        if step == "target":
            await message.reply(
                "Could not access that destination. Check the username or invite the chosen account before continuing."
            )
            logger.warning("Failed to fetch target chat %s: %s", identifier, err)
        else:
            await message.reply(
                "Could not access that source chat. Confirm the details or add the bot/user session so it can read messages."
            )
            logger.warning("Failed to fetch source chat %s: %s", identifier, err)
        return

    data: Dict[str, object] = state.setdefault("data", {})  # type: ignore[assignment]
    if step == "target":
        data["target_info"] = chat_info
        state["step"] = "source_menu"

        await clear_add_wizard_cancel_keyboard(client, state)
        menu_chat_id = state.get("chat_id")
        menu_message_id = state.get("menu_message_id")
        if menu_chat_id and menu_message_id:
            updated = await edit_message_content(
                client,
                int(menu_chat_id),
                int(menu_message_id),
                render_source_menu(state),
                reply_markup=add_task_source_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            state["chat_id"] = updated.chat.id
            state["menu_message_id"] = updated.id

        await message.reply(
            f"✅ Destination set to {chat_info.display_name} ({chat_info.chat_id}).\n"
            "Tap \"Use Source Channel/Group\" to continue.",
            reply_markup=remove_cancel_keyboard(),
        )
        await set_add_wizard_bottom_bar(
            client, state, add_task_prompt_source_bottom_bar()
        )
        return

    data["source_info"] = chat_info
    target_info: ChatAccessInfo = data["target_info"]  # type: ignore[assignment]

    await clear_add_wizard_cancel_keyboard(client, state)
    await clear_add_wizard_bottom_bar(client, state)

    task = STORE.add_task(
        user_id,
        source_id=chat_info.chat_id,
        source_name=chat_info.display_name,
        target_id=target_info.chat_id,
        target_name=target_info.display_name,
        media_types=["all"],
        caption=None,
    )

    menu_chat_id = state.get("chat_id")
    menu_message_id = state.get("menu_message_id")
    if menu_chat_id and menu_message_id:
        await edit_message_content(
            client,
            int(menu_chat_id),
            int(menu_message_id),
            await build_start_caption(
                client, message.from_user.first_name if message.from_user else None
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    chat_id = int(state.get("chat_id", message.chat.id))
    await conclude_add_wizard(client, user_id, chat_id, task)


async def handle_filters_command_input(
    client: Client, message: Message, state: Dict[str, object]
) -> None:
    task: ForwardTask = state["task"]  # type: ignore[assignment]
    media_types = normalise_media_types(message.text.split(","))
    if not media_types:
        await message.reply("Invalid media types. Try again.")
        return

    updated = replace(task, media_types=list(media_types))
    STORE.update_task(updated)
    await reset_action_with_cleanup(client, message.from_user.id)
    await message.reply(
        "Media filters updated.\n\n" + render_task(updated),
        reply_markup=task_actions_keyboard(updated),
        parse_mode=ParseMode.HTML,
    )


async def handle_caption_input(
    client: Client, message: Message, state: Dict[str, object]
) -> None:
    task: ForwardTask = state["task"]  # type: ignore[assignment]
    text = message.text.strip()
    if text == "-":
        caption = None
    else:
        caption = text

    updated = replace(task, caption=caption)
    STORE.update_task(updated)
    summary_chat_id = state.get("chat_id")
    summary_message_id = state.get("summary_message_id")
    await reset_action_with_cleanup(client, message.from_user.id)
    if summary_chat_id and summary_message_id:
        try:
            await client.edit_message_text(
                summary_chat_id,
                summary_message_id,
                "Caption updated.\n\n" + render_task(updated),
                reply_markup=task_actions_keyboard(updated),
                parse_mode=ParseMode.HTML,
            )
        except RPCError as err:
            logger.debug("Unable to edit caption update message: %s", err)
    else:
        await message.reply(
            "Caption updated.\n\n" + render_task(updated),
            reply_markup=task_actions_keyboard(updated),
            parse_mode=ParseMode.HTML,
        )


async def handle_size_input(
    client: Client, message: Message, state: Dict[str, object]
) -> None:
    task: ForwardTask = state["task"]  # type: ignore[assignment]
    if not message.text:
        await message.reply("Send a size value in megabytes.")
        return

    mode = state.get("mode")
    text = message.text.strip()

    if mode == "max":
        if text == "-":
            max_size = None
        else:
            try:
                _, max_size = parse_size_limits(f"0-{text}")
            except ValueError as err:
                await message.reply(str(err))
                return
        updated = replace(task, max_media_size=max_size)
        STORE.update_task(updated)
        state["task"] = updated
        state["mode"] = None
        await update_size_panel(
            client,
            state,
            updated,
            note="✅ Maximum size updated.",
        )
        return

    if mode == "min":
        if text == "-":
            min_size = None
        else:
            try:
                min_size, _ = parse_size_limits(f"{text}-")
            except ValueError as err:
                await message.reply(str(err))
                return
        updated = replace(task, min_media_size=min_size)
        STORE.update_task(updated)
        state["task"] = updated
        state["mode"] = None
        await update_size_panel(
            client,
            state,
            updated,
            note="✅ Minimum size updated.",
        )
        return

    try:
        min_size, max_size = parse_size_limits(text)
    except ValueError as err:
        await message.reply(str(err))
        return

    updated = replace(task, min_media_size=min_size, max_media_size=max_size)
    STORE.update_task(updated)
    state["task"] = updated
    state["mode"] = None
    await update_size_panel(
        client,
        state,
        updated,
        note="✅ Size limits updated.",
    )


@APP.on_message(~filters.private)
async def forward_router(client: Client, message: Message) -> None:
    if message.chat.type not in {ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL}:
        return

    tasks = STORE.get_tasks_for_source(message.chat.id)
    if not tasks:
        return

    for task in tasks:
        await send_forward(client, message, task)
