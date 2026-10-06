"""Calendar of due dates: each task's next due date and later ones, assuming each is done on time."""
from __future__ import annotations

import datetime as dt

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import engine
from .const import DOMAIN
from .entity import BedekEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    add([MaintenanceCalendar(entry)])


class MaintenanceCalendar(BedekEntity, CalendarEntity):
    _attr_translation_key = "maintenance"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "calendar")
        self.entity_id = f"calendar.{DOMAIN}"

    def _events(self, start: dt.date, end: dt.date) -> list[CalendarEvent]:
        runtime = self.runtime
        today = runtime.today()
        out = []
        for task in runtime.store.tasks.values():
            for day in engine.project(task, start, end, today, runtime.entity_due(task)):
                out.append(
                    CalendarEvent(
                        start=day,
                        end=day + dt.timedelta(days=1),
                        summary=task["name"],
                        description=task.get("notes") or None,
                        uid=f"{task['id']}-{day.isoformat()}",
                    )
                )
        out.sort(key=lambda e: (e.start, e.summary))
        return out

    @property
    def event(self) -> CalendarEvent | None:
        today = self.runtime.today()
        events = self._events(today, today + dt.timedelta(days=800))
        return events[0] if events else None

    async def async_get_events(self, hass: HomeAssistant, start_date: dt.datetime, end_date: dt.datetime) -> list[CalendarEvent]:
        start = dt_util.as_local(start_date).date()
        end = dt_util.as_local(end_date).date() + dt.timedelta(days=1)
        return [
            e for e in self._events(start, end)
            if dt_util.start_of_local_day(e.end) > start_date and dt_util.start_of_local_day(e.start) < end_date
        ]
