"""Per-entry runtime: tasks, computed state, daily refresh, reminders, mobile actions."""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_point_in_time, async_track_state_change_event
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util

from . import engine
from .const import (
    ACTION_DONE,
    ACTION_PREFIX,
    ACTION_SNOOZE,
    ATTENTION,
    CONF_DIASPORA,
    CONF_LANGUAGE,
    CONF_NOTIFY_TARGETS,
    CONF_QUIET_ON_SHABBAT,
    CONF_REMIND_DAYS,
    CONF_REMINDER_TIME,
    CONF_REPEAT_DAYS,
    CONF_SNOOZE_DAYS,
    DEFAULT_REMIND_DAYS,
    DEFAULT_REMINDER_TIME,
    DEFAULT_REPEAT_DAYS,
    DEFAULT_SNOOZE_DAYS,
    DOMAIN,
    EVENT_COMPLETED,
    EVENT_REMINDER,
    LANG_AUTO,
    PANEL_URL_PATH,
    SCHED_ENTITY,
    SIGNAL_TASK_ADDED,
    SIGNAL_UPDATED,
    ST_DUE,
    ST_OVERDUE,
    ST_SOON,
    STATUSES,
)
from .storage import TaskStore, ValidationError, validate_completion, validate_task

LOG = logging.getLogger(__name__)
CATCH_UP_UNTIL = dt.time(21, 0)

TEXT = {
    "title": ("Bedek Bayit", "בדק בית"),
    ST_SOON: ("{t}: due in {n} days", "{t}: בעוד {n} ימים"),
    "soon_1": ("{t}: due tomorrow", "{t}: מחר"),
    ST_DUE: ("{t}: due today", "{t}: היום"),
    ST_OVERDUE: ("{t}: overdue by {n} days", "{t}: באיחור של {n} ימים"),
    "overdue_1": ("{t}: overdue since yesterday", "{t}: באיחור מאתמול"),
    "many": ("{n} maintenance tasks need attention", "{n} משימות תחזוקה דורשות טיפול"),
    "done": ("Done", "בוצע"),
    "snooze": ("Snooze {n} days", "דחייה ב-{n} ימים"),
}


def parse_time(value: str | None) -> dt.time:
    try:
        hours, minutes = str(value or DEFAULT_REMINDER_TIME).split(":")[:2]
        return dt.time(int(hours), int(minutes))
    except (TypeError, ValueError):
        return dt.time(9, 0)


class BedekRuntime:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.store = TaskStore(hass, entry.entry_id)
        opts = entry.options
        self.remind_days = int(opts.get(CONF_REMIND_DAYS, DEFAULT_REMIND_DAYS))
        self.repeat_days = int(opts.get(CONF_REPEAT_DAYS, DEFAULT_REPEAT_DAYS))
        self.snooze_days = int(opts.get(CONF_SNOOZE_DAYS, DEFAULT_SNOOZE_DAYS))
        self.targets: list[str] = [t for t in opts.get(CONF_NOTIFY_TARGETS, []) if t]
        self.reminder_time = parse_time(opts.get(CONF_REMINDER_TIME))
        self.quiet = bool(opts.get(CONF_QUIET_ON_SHABBAT, True))
        self.diaspora = bool(opts.get(CONF_DIASPORA, False))
        self._unsubs: list[CALLBACK_TYPE] = []
        self._entity_unsub: CALLBACK_TYPE | None = None
        self._lock = asyncio.Lock()
        self._listeners: set[CALLBACK_TYPE] = set()

    # ---- lifecycle -------------------------------------------------------

    async def async_start(self) -> None:
        await self.store.async_load()
        self._track_entities()
        self._schedule_midnight()
        self._schedule_reminders()
        self._unsubs.append(self.hass.bus.async_listen("mobile_app_notification_action", self._on_action))
        self._unsubs.append(async_at_started(self.hass, self._catch_up))

    async def _catch_up(self, _hass: HomeAssistant) -> None:
        """Restarted after today's reminder time: send what is pending (not late at night)."""
        now = dt_util.now().time()
        if self.reminder_time <= now < CATCH_UP_UNTIL:
            await self.async_send_reminders()

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._entity_unsub:
            self._entity_unsub()
            self._entity_unsub = None

    def _schedule_midnight(self) -> None:
        now = dt_util.now()
        at = dt_util.start_of_local_day(now + dt.timedelta(days=1)) + dt.timedelta(seconds=5)

        @callback
        def _fire(_now: dt.datetime) -> None:
            self._schedule_midnight()
            self.async_notify_changed()

        self._unsubs.append(async_track_point_in_time(self.hass, _fire, at))

    def _schedule_reminders(self) -> None:
        now = dt_util.now()
        at = dt.datetime.combine(now.date(), self.reminder_time, dt_util.get_default_time_zone())
        if at <= now:
            at = dt.datetime.combine(now.date() + dt.timedelta(days=1), self.reminder_time, at.tzinfo)

        async def _fire(_now: dt.datetime) -> None:
            self._schedule_reminders()
            await self.async_send_reminders()

        self._unsubs.append(async_track_point_in_time(self.hass, _fire, at))

    def _track_entities(self) -> None:
        if self._entity_unsub:
            self._entity_unsub()
            self._entity_unsub = None
        ids = sorted(
            {t["schedule"]["entity_id"] for t in self.store.tasks.values() if t["schedule"]["type"] == SCHED_ENTITY}
        )
        if not ids:
            return

        @callback
        def _changed(_event: Event[EventStateChangedData]) -> None:
            self.async_notify_changed()

        self._entity_unsub = async_track_state_change_event(self.hass, ids, _changed)

    # ---- computed state --------------------------------------------------

    def today(self) -> dt.date:
        return dt_util.now().date()

    def language(self, hass_language: str | None = None) -> str:
        lang = self.entry.options.get(CONF_LANGUAGE, LANG_AUTO)
        if lang == LANG_AUTO:
            lang = hass_language or str(self.hass.config.language or "en")
        return "he" if lang.startswith("he") else "en"

    def entity_due(self, task: dict[str, Any]) -> dt.date | None:
        if task["schedule"]["type"] != SCHED_ENTITY:
            return None
        state = self.hass.states.get(task["schedule"]["entity_id"])
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, ""):
            return None
        parsed = dt_util.parse_datetime(state.state)
        if parsed is not None:
            return dt_util.as_local(parsed).date() if parsed.tzinfo else parsed.date()
        return engine.parse_date(state.state)

    def due(self, task: dict[str, Any], today: dt.date | None = None) -> dt.date | None:
        return engine.next_due(task, today or self.today(), self.entity_due(task))

    def remind_for(self, task: dict[str, Any]) -> int:
        value = task.get("remind_days")
        return self.remind_days if value is None else int(value)

    def view(self, task: dict[str, Any], today: dt.date | None = None) -> dict[str, Any]:
        """Task plus computed fields (WS / entity attributes)."""
        today = today or self.today()
        due = self.due(task, today)
        return {
            **task,
            "due": due.isoformat() if due else None,
            "days_left": (due - today).days if due else None,
            "status": engine.status(task, due, today, self.remind_for(task)),
            "progress": engine.progress(task, due, today),
            "effective_remind_days": self.remind_for(task),
        }

    def views(self) -> list[dict[str, Any]]:
        today = self.today()
        items = [self.view(t, today) for t in self.store.tasks.values()]
        items.sort(
            key=lambda v: (
                STATUSES.index(v["status"]),
                v["due"] or "9999",
                v["name"],
            )
        )
        return items

    def counts(self) -> dict[str, int]:
        out = {s: 0 for s in STATUSES}
        today = self.today()
        for task in self.store.tasks.values():
            out[self.view(task, today)["status"]] += 1
        return out

    # ---- change notification --------------------------------------------

    @callback
    def async_notify_changed(self) -> None:
        async_dispatcher_send(self.hass, f"{SIGNAL_UPDATED}_{self.entry.entry_id}")
        for listener in list(self._listeners):
            listener()

    @callback
    def async_listen(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    async def _commit(self) -> None:
        await self.store.async_save()
        self._track_entities()
        self.async_notify_changed()

    # ---- mutations -------------------------------------------------------

    def get(self, task_id: str) -> dict[str, Any]:
        task = self.store.tasks.get(task_id)
        if task is None:
            raise ValidationError({"task_id": "not_found"})
        return task

    async def async_save_task(self, data: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            task_id = data.get("id")
            existing = self.get(task_id) if task_id else None
            task = validate_task(data, self.today(), existing)
            is_new = existing is None
            self.store.add(task)
            await self._commit()
        if is_new:
            async_dispatcher_send(self.hass, f"{SIGNAL_TASK_ADDED}_{self.entry.entry_id}", task["id"])
        return self.view(task)

    async def async_remove_task(self, task_id: str) -> None:
        async with self._lock:
            self.get(task_id)
            del self.store.tasks[task_id]
            await self._commit()

    async def async_complete(self, task_id: str, data: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
        async with self._lock:
            task = self.get(task_id)
            day, note, cost = validate_completion(data, self.today())
            user = None
            if user_id and (u := await self.hass.auth.async_get_user(user_id)):
                user = u.name
            self.store.record(task, day, note, cost, user)
            self.store.notified.pop(task_id, None)
            await self._commit()
        self.hass.bus.async_fire(
            EVENT_COMPLETED, {"task_id": task_id, "name": task["name"], "date": day.isoformat(), "cost": cost}
        )
        return self.view(task)

    async def async_snooze(self, task_id: str, days: int | None = None) -> dict[str, Any]:
        async with self._lock:
            task = self.get(task_id)
            days = self.snooze_days if days is None else days
            if not 1 <= int(days) <= 365:
                raise ValidationError({"days": "invalid"})
            task["snoozed_until"] = (self.today() + dt.timedelta(days=int(days))).isoformat()
            await self._commit()
        return self.view(task)

    async def async_delete_history(self, task_id: str, index: int) -> dict[str, Any]:
        async with self._lock:
            task = self.get(task_id)
            history = task.get("history", [])
            if not 0 <= index < len(history):
                raise ValidationError({"index": "invalid"})
            removed = history.pop(index)
            if removed["date"] == task.get("last_done"):
                task["last_done"] = history[0]["date"] if history else task.get("last_done")
            await self._commit()
        return self.view(task)

    # ---- reminders -------------------------------------------------------

    def _text(self, key: str, lang: str, **kw: Any) -> str:
        en, he = TEXT[key]
        return (he if lang == "he" else en).format(**kw)

    def message(self, view: dict[str, Any], lang: str) -> str:
        status, days, name = view["status"], view["days_left"], view["name"]
        if status == ST_SOON:
            return self._text("soon_1" if days == 1 else ST_SOON, lang, t=name, n=days)
        if status == ST_OVERDUE:
            return self._text("overdue_1" if days == -1 else ST_OVERDUE, lang, t=name, n=-days)
        return self._text(ST_DUE, lang, t=name)

    def pending_reminders(self, today: dt.date) -> list[dict[str, Any]]:
        """Tasks whose reminder phase changed, or overdue ones due for a repeat."""
        out = []
        for task in self.store.tasks.values():
            view = self.view(task, today)
            phase = view["status"]
            if phase not in ATTENTION:
                continue
            sent = self.store.notified.get(task["id"])
            if sent and sent.get("due") == view["due"]:
                if sent.get("phase") == phase:
                    last = engine.parse_date(sent.get("date"))
                    if phase != ST_OVERDUE or self.repeat_days <= 0 or last is None:
                        continue
                    if (today - last).days < self.repeat_days:
                        continue
            out.append(view)
        return out

    async def async_send_reminders(self) -> int:
        today = self.today()
        if self.quiet and await self.hass.async_add_executor_job(engine.is_quiet_day, today, self.diaspora):
            return 0
        pending = self.pending_reminders(today)
        if not pending:
            return 0
        lang = self.language()
        for view in pending:
            self.store.notified[view["id"]] = {"due": view["due"], "phase": view["status"], "date": today.isoformat()}
            self.hass.bus.async_fire(
                EVENT_REMINDER,
                {"task_id": view["id"], "name": view["name"], "status": view["status"], "due": view["due"],
                 "days_left": view["days_left"], "message": self.message(view, lang)},
            )
        await self.store.async_save()
        if self.targets:
            await self._notify(pending, lang)
        return len(pending)

    async def _notify(self, pending: list[dict[str, Any]], lang: str) -> None:
        title = self._text("title", lang)
        if len(pending) == 1:
            view = pending[0]
            message = self.message(view, lang)
            data: dict[str, Any] = {
                "tag": f"{DOMAIN}_{view['id']}",
                "url": f"/{PANEL_URL_PATH}",
                "clickAction": f"/{PANEL_URL_PATH}",
                "actions": [
                    {"action": f"{ACTION_PREFIX}{ACTION_DONE}_{view['id']}", "title": self._text("done", lang)},
                    {"action": f"{ACTION_PREFIX}{ACTION_SNOOZE}_{view['id']}",
                     "title": self._text("snooze", lang, n=self.snooze_days)},
                ],
            }
        else:
            message = self._text("many", lang, n=len(pending)) + ":\n" + "\n".join(
                f"• {self.message(v, lang)}" for v in pending
            )
            data = {"tag": DOMAIN, "url": f"/{PANEL_URL_PATH}", "clickAction": f"/{PANEL_URL_PATH}"}
        for target in self.targets:
            domain, _, service = target.partition(".")
            if not service:
                domain, service = "notify", target
            try:
                await self.hass.services.async_call(
                    domain, service, {"title": title, "message": message, "data": data}, blocking=True
                )
            except Exception as err:  # noqa: BLE001 - one broken target must not stop the others
                LOG.warning("Bedek Bayit: notify %s failed: %s", target, err)

    async def _on_action(self, event: Event) -> None:
        action = str(event.data.get("action") or "")
        if not action.startswith(ACTION_PREFIX):
            return
        kind, _, task_id = action[len(ACTION_PREFIX):].partition("_")
        if task_id not in self.store.tasks:
            return
        try:
            if kind == ACTION_DONE:
                await self.async_complete(task_id, {}, event.context.user_id)
            elif kind == ACTION_SNOOZE:
                await self.async_snooze(task_id)
        except ValidationError as err:
            LOG.warning("Bedek Bayit: notification action failed: %s", err)
