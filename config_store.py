from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DEFAULT_MAX_MEDIA_SIZE_MB = 4000
DEFAULT_MAX_MEDIA_SIZE = DEFAULT_MAX_MEDIA_SIZE_MB * 1024 * 1024


@dataclass
class ForwardTask:
    """Represents a single forwarding rule configured by a user."""

    task_id: int
    owner_id: int
    source_id: int
    source_name: str
    target_id: int
    target_name: str
    media_types: List[str] = field(default_factory=lambda: ["all"])
    caption: Optional[str] = None
    forward_replies: bool = True
    min_media_size: Optional[int] = None
    max_media_size: Optional[int] = None
    skip_duplicates: bool = False
    remove_links: bool = False


class ConfigStore:
    """Persistent storage for per-user forwarding tasks."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.users: Dict[int, Dict[str, object]] = {}
        self.source_index: Dict[int, List[ForwardTask]] = {}

    # ------------------------------------------------------------------
    # Helpers for loading / saving
    # ------------------------------------------------------------------
    def load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._save_to_disk()
            return

        with self.path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.users = {}
        for user_id_str, payload in raw_data.get("users", {}).items():
            user_id = int(user_id_str)
            next_id = int(payload.get("next_task_id", 1))
            tasks_payload = payload.get("tasks", [])
            tasks = [self._task_from_json(user_id, task_json) for task_json in tasks_payload]
            self.users[user_id] = {
                "next_task_id": next_id,
                "tasks": tasks,
            }

        self._rebuild_index()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "users": {
                str(user_id): {
                    "next_task_id": payload["next_task_id"],
                    "tasks": [self._task_to_json(task) for task in payload["tasks"]],
                }
                for user_id, payload in self.users.items()
            }
        }

        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_to_disk(self) -> None:
        self.save()

    # ------------------------------------------------------------------
    # Task manipulation
    # ------------------------------------------------------------------
    def list_tasks(self, owner_id: int) -> List[ForwardTask]:
        payload = self.users.get(owner_id)
        if not payload:
            return []
        return list(payload["tasks"])

    def add_task(
        self,
        owner_id: int,
        *,
        source_id: int,
        source_name: str,
        target_id: int,
        target_name: str,
        media_types: Iterable[str],
        caption: Optional[str] = None,
        forward_replies: bool = True,
        min_media_size: Optional[int] = None,
        max_media_size: Optional[int] = None,
    ) -> ForwardTask:
        payload = self.users.setdefault(owner_id, {"next_task_id": 1, "tasks": []})
        task_id = payload["next_task_id"]
        payload["next_task_id"] = task_id + 1

        max_media_size = (
            DEFAULT_MAX_MEDIA_SIZE if max_media_size is None else max_media_size
        )

        task = ForwardTask(
            task_id=task_id,
            owner_id=owner_id,
            source_id=source_id,
            source_name=source_name,
            target_id=target_id,
            target_name=target_name,
            media_types=list(media_types) or ["all"],
            caption=caption or None,
            forward_replies=forward_replies,
            min_media_size=min_media_size,
            max_media_size=max_media_size,
            skip_duplicates=False,
            remove_links=False,
        )

        payload["tasks"].append(task)
        self._index_task(task)
        self.save()
        return task

    def get_task(self, owner_id: int, task_id: int) -> Optional[ForwardTask]:
        for task in self.list_tasks(owner_id):
            if task.task_id == task_id:
                return task
        return None

    def remove_task(self, owner_id: int, task_id: int) -> bool:
        payload = self.users.get(owner_id)
        if not payload:
            return False

        tasks: List[ForwardTask] = payload["tasks"]
        for index, task in enumerate(tasks):
            if task.task_id == task_id:
                tasks.pop(index)
                self._rebuild_index()
                self.save()
                return True
        return False

    def update_task(self, task: ForwardTask) -> None:
        owner_payload = self.users.get(task.owner_id)
        if not owner_payload:
            return
        for idx, existing in enumerate(owner_payload["tasks"]):
            if existing.task_id == task.task_id:
                owner_payload["tasks"][idx] = task
                break
        self._rebuild_index()
        self.save()

    def get_tasks_for_source(self, source_id: int) -> List[ForwardTask]:
        return list(self.source_index.get(source_id, []))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _rebuild_index(self) -> None:
        self.source_index.clear()
        for payload in self.users.values():
            for task in payload["tasks"]:
                self._index_task(task)

    def _index_task(self, task: ForwardTask) -> None:
        self.source_index.setdefault(task.source_id, []).append(task)

    @staticmethod
    def _task_to_json(task: ForwardTask) -> Dict[str, object]:
        return {
            "task_id": task.task_id,
            "source_id": task.source_id,
            "source_name": task.source_name,
            "target_id": task.target_id,
            "target_name": task.target_name,
            "media_types": task.media_types,
            "caption": task.caption,
            "forward_replies": task.forward_replies,
            "min_media_size": task.min_media_size,
            "max_media_size": task.max_media_size,
            "skip_duplicates": task.skip_duplicates,
            "remove_links": task.remove_links,
        }

    @staticmethod
    def _task_from_json(owner_id: int, payload: Dict[str, object]) -> ForwardTask:
        return ForwardTask(
            task_id=int(payload.get("task_id", 0)),
            owner_id=owner_id,
            source_id=int(payload.get("source_id")),
            source_name=str(payload.get("source_name", "Unknown")),
            target_id=int(payload.get("target_id")),
            target_name=str(payload.get("target_name", "Unknown")),
            media_types=list(payload.get("media_types", ["all"])),
            caption=payload.get("caption"),
            forward_replies=bool(payload.get("forward_replies", True)),
            min_media_size=(
                int(payload.get("min_media_size"))
                if payload.get("min_media_size") is not None
                else None
            ),
            max_media_size=(
                int(payload.get("max_media_size"))
                if payload.get("max_media_size") is not None
                else DEFAULT_MAX_MEDIA_SIZE
            ),
            skip_duplicates=bool(payload.get("skip_duplicates", False)),
            remove_links=bool(payload.get("remove_links", False)),
        )

