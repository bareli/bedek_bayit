"""Config flow, entities, services, WebSocket, reminders."""
from __future__ import annotations

import datetime as dt

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from custom_components.bedek_bayit.config_flow import validate_options
from custom_components.bedek_bayit.const import DOMAIN, EVENT_COMPLETED, EVENT_REMINDER

from .conftest import make_entry, setup_entry

NOW = "2026-10-06 10:00:00+03:00"  # Tuesday
INTERVAL = {"type": "interval", "every": 1, "unit": "months"}


async def add(hass, **kw):
    data = {"name": "AC filter", "schedule_type": "interval", "every": 1, "unit": "months", **kw}
    res = await hass.services.async_call(DOMAIN, "add_task", data, blocking=True, return_response=True)
    await hass.async_block_till_done()
    return res["task_id"]


@pytest.mark.freeze_time(NOW)
async def test_config_flow_seeds_templates(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(result["flow_id"], {"templates": ["nope"]})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"templates": ["ac_filter", "chimney"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data["templates"] == []  # seeded once
    assert hass.states.get("sensor.bedek_bayit_ac_filter").state == "unknown"
    chimney = hass.states.get("sensor.bedek_bayit_chimney")
    assert chimney.state == "2027-04-08"  # two weeks before Pesach 5787
    assert chimney.attributes["status"] == "ok"
    assert hass.states.get("button.bedek_bayit_chimney_done") is not None
    assert hass.states.get("sensor.bedek_bayit_attention").state == "0"
    assert hass.states.get("todo.bedek_bayit") is not None
    assert hass.states.get("calendar.bedek_bayit") is not None

    again = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert again["type"] is FlowResultType.ABORT


async def test_hebrew_seed_names(hass: HomeAssistant):
    await hass.config.async_update(language="he")
    entry = make_entry(hass, templates=["tami4_filter"])
    runtime = await setup_entry(hass, entry)
    (task,) = runtime.store.tasks.values()
    assert task["name"] == "החלפת פילטר תמי4"
    # entity id stays English
    assert hass.states.get("sensor.bedek_bayit_tami4_filter").name.endswith("החלפת פילטר תמי4")


async def test_options_validation(hass: HomeAssistant):
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    res = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"notify_targets": ["light.kitchen"], "reminder_time": "09:00:00", "remind_days": 7,
         "repeat_days": 3, "snooze_days": 7, "quiet_on_shabbat": True, "diaspora": False, "language": "auto"},
    )
    assert res["type"] is FlowResultType.FORM
    assert res["errors"] == {"notify_targets": "invalid_target"}
    # server-side checks behind the selectors
    _, errors = validate_options({"remind_days": 400, "repeat_days": 1.5, "snooze_days": 0, "reminder_time": "25:00",
                                  "notify_targets": ["notify."], "language": "fr"})
    assert errors == {"remind_days": "invalid_days", "repeat_days": "invalid_days", "snooze_days": "invalid_days",
                      "reminder_time": "invalid_time", "notify_targets": "invalid_target", "language": "invalid"}
    res = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"notify_targets": ["notify.phone"], "reminder_time": "08:30:00", "remind_days": 5,
         "repeat_days": 0, "snooze_days": 3, "quiet_on_shabbat": False, "diaspora": False, "language": "he"},
    )
    assert res["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["reminder_time"] == "08:30"
    assert entry.options["remind_days"] == 5
    assert entry.runtime_data.snooze_days == 3


@pytest.mark.freeze_time(NOW)
async def test_add_complete_remove_entities(hass: HomeAssistant):
    runtime = await setup_entry(hass, make_entry(hass))
    events = []
    hass.bus.async_listen(EVENT_COMPLETED, events.append)
    task_id = await add(hass, last_done=dt.date(2026, 9, 1), notes="living room")
    state = hass.states.get("sensor.bedek_bayit_ac_filter")
    assert state.state == "2026-10-01"
    assert state.attributes["status"] == "overdue"
    assert state.attributes["days_left"] == -5
    assert hass.states.get("sensor.bedek_bayit_attention").state == "1"
    assert hass.states.get("todo.bedek_bayit").state == "1"

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.bedek_bayit_ac_filter_done"}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.bedek_bayit_ac_filter")
    assert state.state == "2026-11-06"
    assert state.attributes["status"] == "ok"
    assert state.attributes["last_done"] == "2026-10-06"
    assert hass.states.get("sensor.bedek_bayit_attention").state == "0"
    assert events[0].data["task_id"] == task_id

    await hass.services.async_call(
        DOMAIN, "complete_task",
        {"entity_id": "sensor.bedek_bayit_ac_filter", "date": "2026-10-04", "note": "tech", "cost": 250},
        blocking=True,
    )
    task = runtime.store.tasks[task_id]
    assert task["last_done"] == "2026-10-06"  # older completion only joins the history
    assert [h["date"] for h in task["history"]] == ["2026-10-06", "2026-10-04"]
    assert task["history"][1]["cost"] == 250

    await hass.services.async_call(DOMAIN, "remove_task", {"task_id": task_id}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bedek_bayit_ac_filter") is None
    assert hass.states.get("button.bedek_bayit_ac_filter_done") is None
    assert er.async_get(hass).async_get("sensor.bedek_bayit_ac_filter") is None


@pytest.mark.freeze_time(NOW)
async def test_service_errors(hass: HomeAssistant):
    await setup_entry(hass, make_entry(hass))
    from homeassistant.exceptions import ServiceValidationError

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "complete_task", {"task_id": "missing"}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "complete_task", {}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await add(hass, every=0)
    task_id = await add(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "complete_task", {"task_id": task_id, "date": "2026-12-01"}, blocking=True
        )


@pytest.mark.freeze_time(NOW)
async def test_todo_complete_and_persistence(hass: HomeAssistant):
    entry = make_entry(hass)
    runtime = await setup_entry(hass, entry)
    task_id = await add(hass, last_done=dt.date(2026, 9, 8))  # due 8 Oct: soon
    items = await hass.services.async_call(
        "todo", "get_items", {"entity_id": "todo.bedek_bayit"}, blocking=True, return_response=True
    )
    (item,) = items["todo.bedek_bayit"]["items"]
    assert item["uid"] == task_id and item["due"] == "2026-10-08"
    await hass.services.async_call(
        "todo", "update_item", {"entity_id": "todo.bedek_bayit", "item": task_id, "status": "completed"}, blocking=True
    )
    await hass.async_block_till_done()
    assert runtime.store.tasks[task_id]["last_done"] == "2026-10-06"
    assert hass.states.get("todo.bedek_bayit").state == "0"

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.store.tasks[task_id]["last_done"] == "2026-10-06"
    assert hass.states.get("sensor.bedek_bayit_ac_filter").state == "2026-11-06"


@pytest.mark.freeze_time(NOW)
async def test_calendar_events(hass: HomeAssistant):
    await setup_entry(hass, make_entry(hass))
    await add(hass, every=3, last_done=dt.date(2026, 9, 1))
    await add(hass, name="Chimney", schedule_type="holiday", holiday="pesach", offset_days=-14)
    res = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": "calendar.bedek_bayit", "start_date_time": "2026-10-01 00:00:00", "end_date_time": "2027-06-01 00:00:00"},
        blocking=True, return_response=True,
    )
    events = [(e["start"], e["summary"]) for e in res["calendar.bedek_bayit"]["events"]]
    assert events == [
        ("2026-12-01", "AC filter"), ("2027-03-01", "AC filter"), ("2027-04-08", "Chimney")
    ]
    state = hass.states.get("calendar.bedek_bayit")
    assert state.attributes["message"] == "AC filter"


@pytest.mark.freeze_time(NOW)
async def test_entity_schedule_follows_sensor(hass: HomeAssistant):
    runtime = await setup_entry(hass, make_entry(hass))
    hass.states.async_set("sensor.tami4_filter_upcoming_replacement", "2026-10-10T07:00:00+00:00")
    await add(hass, name="Tami4", schedule_type="entity", source_entity="sensor.tami4_filter_upcoming_replacement")
    state = hass.states.get("sensor.bedek_bayit_tami4")
    assert state.state == "2026-10-10"
    assert state.attributes["status"] == "due_soon"
    hass.states.async_set("sensor.tami4_filter_upcoming_replacement", "2027-04-10T07:00:00+00:00")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bedek_bayit_tami4").state == "2027-04-10"
    hass.states.async_set("sensor.tami4_filter_upcoming_replacement", "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bedek_bayit_tami4").attributes["status"] == "unknown"
    assert len(runtime.store.tasks) == 1


async def test_reminders_phases_repeat_and_actions(hass: HomeAssistant, freezer: FrozenDateTimeFactory):
    freezer.move_to("2026-10-05 08:00:00+03:00")  # Monday
    calls = async_mock_service(hass, "notify", "phone")
    entry = make_entry(hass, notify_targets=["notify.phone"], remind_days=3, repeat_days=2)
    runtime = await setup_entry(hass, entry)
    fired = []
    hass.bus.async_listen(EVENT_REMINDER, fired.append)
    task_id = await add(hass, last_done=dt.date(2026, 9, 7))  # due Wed 7 Oct

    async def at(when: str) -> None:
        freezer.move_to(when)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    await at("2026-10-05 09:00:01+03:00")  # 2 days before: soon
    assert len(calls) == 1
    assert calls[0].data["message"] == "AC filter: due in 2 days"
    actions = calls[0].data["data"]["actions"]
    assert actions[0]["action"] == f"BEDEK_BAYIT_DONE_{task_id}"
    assert fired[0].data["status"] == "due_soon"

    await at("2026-10-06 09:00:01+03:00")  # still soon: no repeat
    assert len(calls) == 1
    await at("2026-10-07 09:00:01+03:00")  # due today
    assert calls[-1].data["message"] == "AC filter: due today"
    await at("2026-10-08 09:00:01+03:00")  # overdue (Thursday)
    assert calls[-1].data["message"] == "AC filter: overdue since yesterday"
    assert len(calls) == 3
    await at("2026-10-09 09:00:01+03:00")  # Friday: 1 day since, repeat every 2
    assert len(calls) == 3
    await at("2026-10-10 09:00:01+03:00")  # Shabbat: quiet
    assert len(calls) == 3
    await at("2026-10-11 09:00:01+03:00")  # Sunday: repeat
    assert len(calls) == 4
    assert calls[-1].data["message"] == "AC filter: overdue by 4 days"

    snooze = f"BEDEK_BAYIT_SNOOZE_{task_id}"
    hass.bus.async_fire("mobile_app_notification_action", {"action": snooze})
    await hass.async_block_till_done()
    assert runtime.store.tasks[task_id]["snoozed_until"] == "2026-10-18"
    hass.bus.async_fire("mobile_app_notification_action", {"action": f"BEDEK_BAYIT_DONE_{task_id}"})
    await hass.async_block_till_done()
    task = runtime.store.tasks[task_id]
    assert task["last_done"] == "2026-10-11" and task["snoozed_until"] is None
    hass.bus.async_fire("mobile_app_notification_action", {"action": "BEDEK_BAYIT_DONE_missing"})
    await hass.async_block_till_done()


async def test_reminders_grouped_and_hebrew(hass: HomeAssistant, freezer: FrozenDateTimeFactory):
    freezer.move_to("2026-10-06 08:00:00+03:00")
    calls = async_mock_service(hass, "notify", "phone")
    await setup_entry(hass, make_entry(hass, notify_targets=["notify.phone"], language="he"))
    await add(hass, last_done=dt.date(2026, 9, 1))
    await add(hass, name="Smoke", last_done=dt.date(2026, 9, 6))
    freezer.move_to("2026-10-06 09:00:01+03:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls) == 1
    msg = calls[0].data["message"]
    assert msg.startswith("2 משימות תחזוקה דורשות טיפול")
    assert "AC filter: באיחור של 5 ימים" in msg and "Smoke: היום" in msg
    assert calls[0].data["title"] == "בדק בית"
    assert "actions" not in calls[0].data["data"]


async def test_ws_api(hass: HomeAssistant, hass_ws_client, freezer: FrozenDateTimeFactory):
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": f"{DOMAIN}/subscribe", "language": "he"})
    assert (await client.receive_json())["success"]
    first = await client.receive_json()
    assert first["event"]["tasks"] == []
    assert first["event"]["language"] == "he"
    assert any(t["key"] == "dud_service" and t["name"].startswith("טיפול בדוד") for t in first["event"]["templates"])

    await client.send_json_auto_id({"type": f"{DOMAIN}/task/save", "task": {"name": "", "schedule": {"type": "interval"}}})
    res = await client.receive_json()
    assert res["result"]["ok"] is False
    assert res["result"]["errors"] == {"name": "required", "schedule.unit": "invalid"}

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/task/save", "task": {"name": "Filter", "schedule": INTERVAL, "last_done": "2026-09-06"}}
    )
    res = await client.receive_json()
    if "event" in res:  # subscription push may arrive first
        res, push = await client.receive_json(), res
    else:
        push = await client.receive_json()
    assert res["result"]["ok"] and res["result"]["task"]["status"] == "due"
    task_id = res["result"]["task"]["id"]
    assert push["event"]["tasks"][0]["id"] == task_id

    await client.send_json_auto_id({"type": f"{DOMAIN}/task/complete", "task_id": task_id, "cost": "abc"})
    msgs = [await client.receive_json()]
    assert msgs[0]["result"]["errors"] == {"cost": "invalid"}

    await client.send_json_auto_id({"type": f"{DOMAIN}/task/complete", "task_id": task_id, "note": "done", "cost": 40})
    got = [await client.receive_json(), await client.receive_json()]
    result = next(m for m in got if m.get("type") == "result")
    entry0 = result["result"]["task"]["history"][0]
    assert entry0["note"] == "done" and entry0["cost"] == 40 and entry0["user"]

    await client.send_json_auto_id({"type": f"{DOMAIN}/task/snooze", "task_id": task_id, "days": 0})
    got = await client.receive_json()
    assert got["result"]["errors"] == {"days": "invalid"}

    await client.send_json_auto_id({"type": f"{DOMAIN}/task/delete_history", "task_id": task_id, "index": 0})
    got = [await client.receive_json(), await client.receive_json()]
    result = next(m for m in got if m.get("type") == "result")
    assert result["result"]["task"]["history"] == []

    await client.send_json_auto_id({"type": f"{DOMAIN}/task/delete", "task_id": "nope"})
    got = await client.receive_json()
    assert got["result"]["errors"] == {"task_id": "not_found"}


async def test_ws_non_admin(hass: HomeAssistant, hass_ws_client, hass_read_only_access_token, freezer):
    freezer.move_to(NOW)
    runtime = await setup_entry(hass, make_entry(hass))
    client = await hass_ws_client(hass, hass_read_only_access_token)
    task_id = (await runtime.async_save_task({"name": "x", "schedule": INTERVAL}))["id"]
    await client.send_json_auto_id({"type": f"{DOMAIN}/task/save", "task": {"name": "y", "schedule": INTERVAL}})
    res = await client.receive_json()
    assert not res["success"] and res["error"]["code"] == "unauthorized"
    await client.send_json_auto_id({"type": f"{DOMAIN}/task/delete", "task_id": task_id})
    assert (await client.receive_json())["error"]["code"] == "unauthorized"
    # household members can mark done
    await client.send_json_auto_id({"type": f"{DOMAIN}/task/complete", "task_id": task_id})
    res = await client.receive_json()
    assert res["success"] and res["result"]["ok"]


@pytest.mark.freeze_time(NOW)
async def test_list_tasks_and_unload(hass: HomeAssistant):
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    await add(hass, last_done=dt.date(2026, 9, 1))
    await add(hass, name="Unknown one")
    res = await hass.services.async_call(DOMAIN, "list_tasks", {}, blocking=True, return_response=True)
    assert [t["status"] for t in res["tasks"]] == ["overdue", "unknown"]
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.freeze_time(NOW)
async def test_rename_updates_entity_names_and_catch_up(hass: HomeAssistant):
    runtime = await setup_entry(hass, make_entry(hass))
    task_id = await add(hass, last_done=dt.date(2026, 9, 1))
    assert hass.states.get("button.bedek_bayit_ac_filter_done").name == "Bedek Bayit AC filter: mark done"
    await runtime.async_save_task({"id": task_id, "name": "Salon AC"})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bedek_bayit_ac_filter").name == "Bedek Bayit Salon AC"  # entity id kept
    assert hass.states.get("button.bedek_bayit_ac_filter_done").name == "Bedek Bayit Salon AC: mark done"


async def test_catch_up_after_restart(hass: HomeAssistant, freezer: FrozenDateTimeFactory):
    """Started after today's reminder time: pending reminders go out once, not again on reload."""
    freezer.move_to("2026-10-06 10:00:00+03:00")
    calls = async_mock_service(hass, "notify", "phone")
    entry = make_entry(hass, notify_targets=["notify.phone"])
    runtime = await setup_entry(hass, entry)
    await runtime.async_save_task({"name": "Filter", "schedule": INTERVAL, "last_done": "2026-09-01"})
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(calls) == 1


@pytest.mark.freeze_time(NOW)
async def test_services_admin_only_for_add_remove(hass: HomeAssistant, hass_read_only_user, hass_admin_user):
    from homeassistant.core import Context
    from homeassistant.exceptions import Unauthorized

    runtime = await setup_entry(hass, make_entry(hass))
    task_id = await add(hass)  # no user (automation): allowed
    user = Context(user_id=hass_read_only_user.id)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(DOMAIN, "remove_task", {"task_id": task_id}, blocking=True, context=user)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN, "add_task", {"name": "x", "every": 1}, blocking=True, context=user, return_response=True
        )
    # household members may still mark done and snooze
    await hass.services.async_call(DOMAIN, "complete_task", {"task_id": task_id}, blocking=True, context=user)
    await hass.services.async_call(DOMAIN, "snooze_task", {"task_id": task_id}, blocking=True, context=user)
    await hass.services.async_call(
        DOMAIN, "remove_task", {"task_id": task_id}, blocking=True, context=Context(user_id=hass_admin_user.id)
    )
    assert runtime.store.tasks == {}
