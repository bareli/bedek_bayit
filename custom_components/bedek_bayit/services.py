"""Services: complete / snooze / add / remove / list tasks."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, HOLIDAYS, SCHEDULE_TYPES, UNITS
from .runtime import BedekRuntime
from .storage import ValidationError
from .websocket import resolve_runtime

TARGET = {vol.Optional("task_id"): cv.string, vol.Optional("entity_id"): cv.entity_id}

COMPLETE_SCHEMA = vol.Schema(
    {**TARGET, vol.Optional("date"): cv.date, vol.Optional("note"): cv.string, vol.Optional("cost"): vol.Coerce(float)}
)
SNOOZE_SCHEMA = vol.Schema({**TARGET, vol.Optional("days"): vol.All(vol.Coerce(int), vol.Range(1, 365))})
REMOVE_SCHEMA = vol.Schema(TARGET)
ADD_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("template"): cv.string,
        vol.Optional("category"): cv.string,
        vol.Optional("icon"): cv.icon,
        vol.Optional("schedule_type", default="interval"): vol.In(SCHEDULE_TYPES),
        vol.Optional("every"): vol.Coerce(int),
        vol.Optional("unit", default="months"): vol.In(UNITS),
        vol.Optional("holiday"): vol.In(HOLIDAYS),
        vol.Optional("month"): vol.Coerce(int),
        vol.Optional("day"): vol.Coerce(int),
        vol.Optional("offset_days", default=0): vol.Coerce(int),
        vol.Optional("source_entity"): cv.entity_id,
        vol.Optional("last_done"): cv.date,
        vol.Optional("remind_days"): vol.Coerce(int),
        vol.Optional("notes"): cv.string,
    }
)


def _runtime(hass: HomeAssistant) -> BedekRuntime:
    runtime = resolve_runtime(hass)
    if runtime is None:
        raise ServiceValidationError("Bedek Bayit is not set up")
    return runtime


def _task_id(hass: HomeAssistant, runtime: BedekRuntime, data: dict[str, Any]) -> str:
    if task_id := data.get("task_id"):
        if task_id in runtime.store.tasks:
            return task_id
        raise ServiceValidationError(f"Unknown task: {task_id}")
    entity_id = data.get("entity_id")
    if not entity_id:
        raise ServiceValidationError("Give task_id or entity_id")
    entry = er.async_get(hass).async_get(entity_id)
    prefix = f"{runtime.entry.entry_id}_"
    if entry and entry.platform == DOMAIN and entry.unique_id.startswith(prefix):
        task_id = entry.unique_id[len(prefix):].rsplit("_", 1)[0]
        if task_id in runtime.store.tasks:
            return task_id
    raise ServiceValidationError(f"{entity_id} is not a Bedek Bayit task entity")


async def _require_admin(hass: HomeAssistant, call: ServiceCall) -> None:
    """Adding / removing tasks is admin configuration, as in the WebSocket API.

    A call without a user (automation, script, the system) is allowed.
    """
    user_id = call.context.user_id
    if not user_id:
        return
    user = await hass.auth.async_get_user(user_id)
    if user is None or not user.is_admin:
        raise Unauthorized(context=call.context)


def _errors(err: ValidationError) -> ServiceValidationError:
    return ServiceValidationError(f"Invalid: {err}")


@callback
def async_register_services(hass: HomeAssistant) -> None:
    async def complete(call: ServiceCall) -> None:
        runtime = _runtime(hass)
        data = {k: call.data.get(k) for k in ("note", "cost")}
        if "date" in call.data:
            data["date"] = call.data["date"].isoformat()
        try:
            await runtime.async_complete(_task_id(hass, runtime, call.data), data, call.context.user_id)
        except ValidationError as err:
            raise _errors(err) from err

    async def snooze(call: ServiceCall) -> None:
        runtime = _runtime(hass)
        await runtime.async_snooze(_task_id(hass, runtime, call.data), call.data.get("days"))

    async def remove(call: ServiceCall) -> None:
        await _require_admin(hass, call)
        runtime = _runtime(hass)
        await runtime.async_remove_task(_task_id(hass, runtime, call.data))

    async def add(call: ServiceCall) -> ServiceResponse:
        await _require_admin(hass, call)
        runtime = _runtime(hass)
        d = call.data
        kind = d["schedule_type"]
        schedule: dict[str, Any] = {"type": kind}
        if kind == "interval":
            schedule.update(every=d.get("every"), unit=d["unit"])
        elif kind == "holiday":
            schedule.update(holiday=d.get("holiday"), offset_days=d["offset_days"])
        elif kind == "yearly":
            schedule.update(month=d.get("month"), day=d.get("day"), offset_days=d["offset_days"])
        else:
            schedule["entity_id"] = d.get("source_entity")
        task = {k: d.get(k) for k in ("name", "template", "category", "icon", "remind_days", "notes")}
        task["schedule"] = schedule
        if "last_done" in d:
            task["last_done"] = d["last_done"].isoformat()
        try:
            view = await runtime.async_save_task(task)
        except ValidationError as err:
            raise _errors(err) from err
        return {"task_id": view["id"]}

    async def list_tasks(call: ServiceCall) -> ServiceResponse:
        return {"tasks": _runtime(hass).views()}

    hass.services.async_register(DOMAIN, "complete_task", complete, COMPLETE_SCHEMA)
    hass.services.async_register(DOMAIN, "snooze_task", snooze, SNOOZE_SCHEMA)
    hass.services.async_register(DOMAIN, "remove_task", remove, REMOVE_SCHEMA)
    hass.services.async_register(DOMAIN, "add_task", add, ADD_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(
        DOMAIN, "list_tasks", list_tasks, vol.Schema({}), supports_response=SupportsResponse.ONLY
    )
