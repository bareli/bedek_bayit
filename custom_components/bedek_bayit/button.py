"""One "mark done" button per task."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BedekTaskEntity, object_id, setup_task_platform

SUFFIX = {"en": "mark done", "he": "סמן כבוצע"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    setup_task_platform(hass, entry, add, lambda e, task_id: [TaskDoneButton(e, task_id)])


class TaskDoneButton(BedekTaskEntity, ButtonEntity):
    """Named "<task>: mark done" in the integration language. A plain name, not a translated
    placeholder name: Home Assistant does not re-render those when the task is renamed."""

    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, entry: ConfigEntry, task_id: str) -> None:
        super().__init__(entry, task_id, "done")
        task = entry.runtime_data.store.tasks[task_id]
        self.entity_id = f"button.{object_id(entry.runtime_data, task)}_done"
        self._refresh()

    def _refresh(self) -> None:
        task = self.task
        if task is not None:
            self._attr_name = f"{task['name']}: {SUFFIX[self.runtime.language()]}"

    async def async_press(self) -> None:
        user_id = self._context.user_id if self._context else None
        await self.runtime.async_complete(self.task_id, {}, user_id)
