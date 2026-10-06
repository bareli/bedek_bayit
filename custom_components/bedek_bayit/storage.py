"""Task storage (one Store per entry) and server-side validation."""
from __future__ import annotations

import datetime as dt
import re
import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CATEGORIES,
    DOMAIN,
    HOLIDAYS,
    MAX_COST,
    MAX_DAYS,
    MAX_EVERY,
    MAX_HISTORY,
    MAX_NAME,
    MAX_NOTES,
    MAX_OFFSET_DAYS,
    MAX_TASKS,
    SCHED_ENTITY,
    SCHED_HOLIDAY,
    SCHED_INTERVAL,
    SCHED_YEARLY,
    SCHEDULE_TYPES,
    UNITS,
)
from .engine import parse_date
from .templates import TEMPLATES

STORAGE_VERSION = 1
_ICON = re.compile(r"^[a-z0-9_-]+:[a-z0-9_-]+$")
_ENTITY = re.compile(r"^(sensor|input_datetime|date|datetime)\.[a-z0-9_]+$")
_MONTH_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class ValidationError(Exception):
    """Field -> error code, shown inline in the editor."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__(", ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


def _int(value: Any, low: int, high: int) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if isinstance(value, float) and value != number:
        return None
    return number if low <= number <= high else None


def validate_schedule(raw: Any, errors: dict[str, str]) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("type") not in SCHEDULE_TYPES:
        errors["schedule.type"] = "invalid"
        return {}
    kind = raw["type"]
    out: dict[str, Any] = {"type": kind}
    if kind == SCHED_INTERVAL:
        unit = raw.get("unit")
        if unit not in UNITS:
            errors["schedule.unit"] = "invalid"
            return out
        every = _int(raw.get("every"), 1, MAX_EVERY[unit])
        if every is None:
            errors["schedule.every"] = "invalid"
        out.update(every=every, unit=unit)
    elif kind in (SCHED_HOLIDAY, SCHED_YEARLY):
        if kind == SCHED_HOLIDAY:
            if raw.get("holiday") not in HOLIDAYS:
                errors["schedule.holiday"] = "invalid"
            out["holiday"] = raw.get("holiday")
        else:
            month = _int(raw.get("month"), 1, 12)
            day = _int(raw.get("day"), 1, 31)
            if month is None:
                errors["schedule.month"] = "invalid"
            elif day is None or day > _MONTH_DAYS[month - 1]:
                errors["schedule.day"] = "invalid"
            out.update(month=month, day=day)
        offset = _int(raw.get("offset_days", 0) or 0, -MAX_OFFSET_DAYS, MAX_OFFSET_DAYS)
        if offset is None:
            errors["schedule.offset_days"] = "invalid"
        out["offset_days"] = offset
    else:
        entity_id = str(raw.get("entity_id") or "").strip()
        if not _ENTITY.match(entity_id):
            errors["schedule.entity_id"] = "invalid"
        out["entity_id"] = entity_id
    return out


def validate_task(data: dict[str, Any], today: dt.date, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a clean task (merged over existing for updates) or raise ValidationError."""
    errors: dict[str, str] = {}
    base = dict(existing or {})
    merged = {**base, **{k: v for k, v in data.items() if k != "id"}}

    name = str(merged.get("name") or "").strip()
    if not name:
        errors["name"] = "required"
    elif len(name) > MAX_NAME:
        errors["name"] = "too_long"

    template = merged.get("template") or None
    if template is not None and template not in TEMPLATES:
        errors["template"] = "invalid"

    category = merged.get("category") or (TEMPLATES[template]["category"] if template in TEMPLATES else "general")
    if category not in CATEGORIES:
        errors["category"] = "invalid"

    icon = str(merged.get("icon") or "").strip() or (
        TEMPLATES[template]["icon"] if template in TEMPLATES else "mdi:wrench-outline"
    )
    if not _ICON.match(icon):
        errors["icon"] = "invalid"

    schedule = validate_schedule(merged.get("schedule"), errors)

    last_done_raw = merged.get("last_done")
    last_done = parse_date(last_done_raw)
    if last_done_raw not in (None, "") and last_done is None:
        errors["last_done"] = "invalid"
    elif last_done is not None and last_done > today:
        errors["last_done"] = "future"

    remind_raw = merged.get("remind_days")
    remind_days = None
    if remind_raw not in (None, ""):
        remind_days = _int(remind_raw, 0, MAX_DAYS)
        if remind_days is None:
            errors["remind_days"] = "invalid"

    notes = str(merged.get("notes") or "")
    if len(notes) > MAX_NOTES:
        errors["notes"] = "too_long"

    if errors:
        raise ValidationError(errors)

    return {
        "id": base.get("id") or uuid.uuid4().hex[:10],
        "name": name,
        "template": template,
        "category": category,
        "icon": icon,
        "schedule": schedule,
        "last_done": last_done.isoformat() if last_done else None,
        "remind_days": remind_days,
        "notes": notes,
        "paused": bool(merged.get("paused", False)),
        "snoozed_until": base.get("snoozed_until") if schedule == base.get("schedule") else None,
        "history": list(base.get("history") or []),
        "created": base.get("created") or today.isoformat(),
    }


def validate_completion(data: dict[str, Any], today: dt.date) -> tuple[dt.date, str, float | None]:
    errors: dict[str, str] = {}
    raw = data.get("date")
    day = parse_date(raw) if raw not in (None, "") else today
    if day is None:
        errors["date"] = "invalid"
    elif day > today:
        errors["date"] = "future"
    note = str(data.get("note") or "").strip()
    if len(note) > MAX_NOTES:
        errors["note"] = "too_long"
    cost = data.get("cost")
    if cost in (None, ""):
        cost = None
    else:
        try:
            cost = round(float(cost), 2)
        except (TypeError, ValueError):
            cost = -1
        if not 0 <= cost <= MAX_COST:
            errors["cost"] = "invalid"
    if errors:
        raise ValidationError(errors)
    return day, note, cost


class TaskStore:
    """{"tasks": [task...], "notified": {task_id: {"due", "phase", "date"}}}."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.tasks: dict[str, dict[str, Any]] = {}
        self.notified: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.tasks = {t["id"]: t for t in data.get("tasks", []) if isinstance(t, dict) and t.get("id")}
        self.notified = dict(data.get("notified") or {})

    async def async_save(self) -> None:
        self.notified = {k: v for k, v in self.notified.items() if k in self.tasks}
        await self._store.async_save({"tasks": list(self.tasks.values()), "notified": self.notified})

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def add(self, task: dict[str, Any]) -> None:
        if task["id"] not in self.tasks and len(self.tasks) >= MAX_TASKS:
            raise ValidationError({"base": "too_many"})
        self.tasks[task["id"]] = task

    @staticmethod
    def record(task: dict[str, Any], day: dt.date, note: str, cost: float | None, user: str | None) -> None:
        entry = {"date": day.isoformat(), "note": note, "cost": cost, "user": user}
        history = [entry, *task.get("history", [])]
        history.sort(key=lambda h: h["date"], reverse=True)
        task["history"] = history[:MAX_HISTORY]
        last = task.get("last_done")
        if last is None or day.isoformat() >= last:
            task["last_done"] = day.isoformat()
            task["snoozed_until"] = None
