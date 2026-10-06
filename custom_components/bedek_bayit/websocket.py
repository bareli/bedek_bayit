"""WebSocket API for the card and panel."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback

from .const import CATEGORIES, DOMAIN, HOLIDAYS
from .runtime import BedekRuntime
from .storage import ValidationError
from .templates import TEMPLATES, template_view


def resolve_runtime(hass: HomeAssistant) -> BedekRuntime | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data
    return None


@callback
def async_register(hass: HomeAssistant) -> None:
    for handler in (ws_tasks, ws_subscribe, ws_save, ws_delete, ws_complete, ws_snooze, ws_delete_history):
        websocket_api.async_register_command(hass, handler)


def _payload(runtime: BedekRuntime, language: str | None) -> dict[str, Any]:
    lang = runtime.language(language)
    return {
        "tasks": runtime.views(),
        "today": runtime.today().isoformat(),
        "language": lang,
        "templates": [template_view(k, lang) for k in TEMPLATES],
        "categories": CATEGORIES,
        "holidays": HOLIDAYS,
        "remind_days": runtime.remind_days,
        "snooze_days": runtime.snooze_days,
    }


def _no_runtime(connection, msg) -> None:
    connection.send_error(msg["id"], "not_loaded", "Bedek Bayit is not set up")


async def _run(hass: HomeAssistant, connection, msg, coro_factory) -> None:
    runtime = resolve_runtime(hass)
    if runtime is None:
        _no_runtime(connection, msg)
        return
    try:
        task = await coro_factory(runtime)
    except ValidationError as err:
        connection.send_result(msg["id"], {"ok": False, "errors": err.errors})
        return
    connection.send_result(msg["id"], {"ok": True, "task": task})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/tasks", vol.Optional("language"): str})
@callback
def ws_tasks(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    runtime = resolve_runtime(hass)
    if runtime is None:
        _no_runtime(connection, msg)
        return
    connection.send_result(msg["id"], _payload(runtime, msg.get("language")))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe", vol.Optional("language"): str})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Pushes the full payload now and after every change (and at midnight)."""
    runtime = resolve_runtime(hass)
    if runtime is None:
        _no_runtime(connection, msg)
        return

    @callback
    def _send() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], _payload(runtime, msg.get("language"))))

    connection.subscriptions[msg["id"]] = runtime.async_listen(_send)
    connection.send_result(msg["id"])
    _send()


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/task/save", vol.Required("task"): dict}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    await _run(hass, connection, msg, lambda r: r.async_save_task(msg["task"]))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/task/delete", vol.Required("task_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    async def _remove(runtime: BedekRuntime) -> None:
        await runtime.async_remove_task(msg["task_id"])

    await _run(hass, connection, msg, _remove)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/task/complete",
        vol.Required("task_id"): str,
        vol.Optional("date"): vol.Any(str, None),
        vol.Optional("note"): vol.Any(str, None),
        vol.Optional("cost"): vol.Any(vol.Coerce(float), str, None),
    }
)
@websocket_api.async_response
async def ws_complete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    data = {k: msg.get(k) for k in ("date", "note", "cost")}
    await _run(hass, connection, msg, lambda r: r.async_complete(msg["task_id"], data, connection.user.id))


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/task/snooze", vol.Required("task_id"): str, vol.Optional("days"): int}
)
@websocket_api.async_response
async def ws_snooze(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    await _run(hass, connection, msg, lambda r: r.async_snooze(msg["task_id"], msg.get("days")))


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/task/delete_history", vol.Required("task_id"): str, vol.Required("index"): int}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_delete_history(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    await _run(hass, connection, msg, lambda r: r.async_delete_history(msg["task_id"], msg["index"]))
