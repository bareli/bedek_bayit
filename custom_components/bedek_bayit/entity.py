"""Shared entity base: one service device per entry; per-task entities come and go with tasks."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_TASK_ADDED, SIGNAL_UPDATED
from .runtime import BedekRuntime


class BedekEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Bedek Bayit",
            model="Household maintenance",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def runtime(self) -> BedekRuntime:
        return self._entry.runtime_data

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"{SIGNAL_UPDATED}_{self._entry.entry_id}", self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


def object_id(runtime: BedekRuntime, task: dict[str, Any]) -> str:
    """English-friendly object id: template key, else an ASCII name, else the task id."""
    slug = re.sub(r"[^a-z0-9]+", "_", task["name"].lower()).strip("_")
    key = task.get("template") or slug or task["id"]
    return f"{DOMAIN}_{key}"


class BedekTaskEntity(BedekEntity):
    """Bound to one task; removes itself from the registry when the task is deleted."""

    def __init__(self, entry: ConfigEntry, task_id: str, suffix: str) -> None:
        super().__init__(entry, f"{task_id}_{suffix}")
        self.task_id = task_id
        self._removing = False

    @property
    def task(self) -> dict[str, Any] | None:
        return self.runtime.store.tasks.get(self.task_id)

    @property
    def available(self) -> bool:
        return self.task is not None

    @callback
    def _handle_update(self) -> None:
        if self.task is None:
            if not self._removing:
                self._removing = True
                registry = er.async_get(self.hass)
                if registry.async_get(self.entity_id):
                    registry.async_remove(self.entity_id)
                else:
                    self.hass.async_create_task(self.async_remove(force_remove=True))
            return
        self._refresh()
        self.async_write_ha_state()

    def _refresh(self) -> None:
        """Copy task fields into _attr_*; called before each state write."""


def setup_task_platform(
    hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback, factory
) -> None:
    """Create entities for existing tasks now and for new tasks as they are added."""
    runtime: BedekRuntime = entry.runtime_data
    add([e for task_id in runtime.store.tasks for e in factory(entry, task_id)])

    @callback
    def _added(task_id: str) -> None:
        add(factory(entry, task_id))

    entry.async_on_unload(async_dispatcher_connect(hass, f"{SIGNAL_TASK_ADDED}_{entry.entry_id}", _added))
