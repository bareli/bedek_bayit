"""To-do list of tasks that need attention now; checking one off marks the task done."""
from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTENTION, DOMAIN
from .engine import parse_date
from .entity import BedekEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    add([MaintenanceTodo(entry)])


class MaintenanceTodo(BedekEntity, TodoListEntity):
    _attr_translation_key = "maintenance"
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "todo")
        self.entity_id = f"todo.{DOMAIN}"

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=v["id"],
                summary=v["name"],
                status=TodoItemStatus.NEEDS_ACTION,
                due=parse_date(v["due"]),
                description=v["notes"] or None,
            )
            for v in self.runtime.views()
            if v["status"] in ATTENTION
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        if item.uid not in self.runtime.store.tasks:
            raise HomeAssistantError(f"Unknown task {item.uid}")
        if item.status == TodoItemStatus.COMPLETED:
            user_id = self._context.user_id if self._context else None
            await self.runtime.async_complete(item.uid, {}, user_id)
        else:
            self.async_write_ha_state()
