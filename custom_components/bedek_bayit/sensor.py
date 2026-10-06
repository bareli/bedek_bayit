"""Sensors: one next-due date per task, plus a tasks-needing-attention count."""
from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTENTION, DOMAIN, ST_DUE, ST_OVERDUE, ST_SOON
from .entity import BedekEntity, BedekTaskEntity, object_id, setup_task_platform


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    add([AttentionSensor(entry)])
    setup_task_platform(hass, entry, add, lambda e, task_id: [TaskDueSensor(e, task_id)])


class TaskDueSensor(BedekTaskEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, entry: ConfigEntry, task_id: str) -> None:
        super().__init__(entry, task_id, "due")
        task = entry.runtime_data.store.tasks[task_id]
        self.entity_id = f"sensor.{object_id(entry.runtime_data, task)}"
        self._view: dict[str, Any] = {}
        self._refresh()

    def _refresh(self) -> None:
        task = self.task
        if task is None:
            return
        self._view = self.runtime.view(task)
        self._attr_name = task["name"]
        self._attr_icon = task["icon"]

    @property
    def native_value(self) -> dt.date | None:
        due = self._view.get("due")
        return dt.date.fromisoformat(due) if due else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        v = self._view
        last = v.get("history") or []
        return {
            "task_id": self.task_id,
            "status": v.get("status"),
            "days_left": v.get("days_left"),
            "last_done": v.get("last_done"),
            "progress": v.get("progress"),
            "category": v.get("category"),
            "schedule": v.get("schedule"),
            "snoozed_until": v.get("snoozed_until"),
            "last_cost": last[0].get("cost") if last else None,
            "notes": v.get("notes"),
        }


class AttentionSensor(BedekEntity, SensorEntity):
    _attr_translation_key = "attention"
    _attr_icon = "mdi:home-alert-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "tasks"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "attention")
        self.entity_id = f"sensor.{DOMAIN}_attention"

    @property
    def native_value(self) -> int:
        return sum(1 for v in self.runtime.views() if v["status"] in ATTENTION)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        views = self.runtime.views()
        return {
            "overdue": [v["name"] for v in views if v["status"] == ST_OVERDUE],
            "due_today": [v["name"] for v in views if v["status"] == ST_DUE],
            "due_soon": [v["name"] for v in views if v["status"] == ST_SOON],
            "total": len(views),
        }
