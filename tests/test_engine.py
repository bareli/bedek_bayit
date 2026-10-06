"""Pure scheduling logic."""
from __future__ import annotations

import datetime as dt

import pytest

from custom_components.bedek_bayit import engine
from custom_components.bedek_bayit.storage import ValidationError, validate_completion, validate_task
from custom_components.bedek_bayit.templates import TEMPLATES

D = dt.date


def task(schedule, last_done=None, **kw):
    return {"id": "t1", "name": "x", "schedule": schedule, "last_done": last_done, **kw}


@pytest.mark.parametrize(
    ("start", "every", "unit", "expected"),
    [
        (D(2026, 1, 31), 1, "months", D(2026, 2, 28)),
        (D(2028, 1, 31), 1, "months", D(2028, 2, 29)),
        (D(2026, 11, 15), 3, "months", D(2027, 2, 15)),
        (D(2024, 2, 29), 1, "years", D(2025, 2, 28)),
        (D(2026, 10, 6), 2, "weeks", D(2026, 10, 20)),
        (D(2026, 10, 6), 10, "days", D(2026, 10, 16)),
        (D(2023, 4, 1), 42, "months", D(2026, 10, 1)),
    ],
)
def test_add_interval(start, every, unit, expected):
    assert engine.add_interval(start, every, unit) == expected


@pytest.mark.parametrize(
    ("holiday", "hyear", "expected"),
    [
        ("pesach", 5786, D(2026, 4, 2)),
        ("pesach", 5787, D(2027, 4, 22)),
        ("rosh_hashana", 5787, D(2026, 9, 12)),
        ("sukkot", 5787, D(2026, 9, 26)),
        ("shavuot", 5786, D(2026, 5, 22)),
        ("hanukkah", 5787, D(2026, 12, 5)),
        ("purim", 5786, D(2026, 3, 3)),  # regular year: Adar
        ("purim", 5787, D(2027, 3, 23)),  # leap year: Adar II
    ],
)
def test_holiday_dates(holiday, hyear, expected):
    assert engine.holiday_date(holiday, hyear) == expected


def test_interval_due_and_status():
    t = task({"type": "interval", "every": 1, "unit": "months"}, "2026-09-10")
    today = D(2026, 10, 6)
    due = engine.next_due(t, today)
    assert due == D(2026, 10, 10)
    assert engine.status(t, due, today, 7) == "due_soon"
    assert engine.status(t, due, today, 3) == "ok"
    assert engine.status(t, due, D(2026, 10, 10), 3) == "due"
    assert engine.status(t, due, D(2026, 10, 11), 3) == "overdue"
    assert engine.progress(t, due, today) == round(26 / 30, 3)


def test_never_done_interval_is_unknown():
    t = task({"type": "interval", "every": 6, "unit": "months"})
    assert engine.next_due(t, D(2026, 10, 6)) is None
    assert engine.status(t, None, D(2026, 10, 6), 7) == "unknown"
    assert engine.project(t, D(2026, 1, 1), D(2028, 1, 1), D(2026, 10, 6)) == []


def test_paused():
    t = task({"type": "interval", "every": 1, "unit": "days"}, "2026-01-01", paused=True)
    due = engine.next_due(t, D(2026, 10, 6))
    assert engine.status(t, due, D(2026, 10, 6), 7) == "paused"
    assert engine.project(t, D(2026, 1, 1), D(2028, 1, 1), D(2026, 10, 6)) == []


def test_snooze_only_pushes_later():
    t = task({"type": "interval", "every": 1, "unit": "months"}, "2026-09-01", snoozed_until="2026-10-13")
    assert engine.next_due(t, D(2026, 10, 6)) == D(2026, 10, 13)
    t["snoozed_until"] = "2026-09-20"
    assert engine.next_due(t, D(2026, 10, 6)) == D(2026, 10, 1)


def test_before_pesach_never_done():
    t = task({"type": "holiday", "holiday": "pesach", "offset_days": -14})
    # Pesach 2027 = 22 Apr -> due 8 Apr
    assert engine.next_due(t, D(2026, 10, 6)) == D(2027, 4, 8)
    # on the day itself it is due, not next year
    assert engine.next_due(t, D(2027, 4, 8)) == D(2027, 4, 8)


def test_before_pesach_done_early_counts():
    t = task({"type": "holiday", "holiday": "pesach", "offset_days": -14}, "2027-02-01")
    assert engine.next_due(t, D(2027, 2, 2)) == D(2028, 3, 28)  # Pesach 2028 = 11 Apr
    t["last_done"] = "2026-12-01"  # > 90 days before 8 Apr 2027: does not count
    assert engine.next_due(t, D(2027, 2, 2)) == D(2027, 4, 8)


def test_annual_missed_is_overdue():
    t = task({"type": "holiday", "holiday": "pesach", "offset_days": -14}, "2025-03-20")
    today = D(2026, 10, 6)
    due = engine.next_due(t, today)
    assert due == D(2026, 3, 19)  # Pesach 2026 = 2 Apr
    assert engine.status(t, due, today, 7) == "overdue"


def test_after_sukkot():
    t = task({"type": "holiday", "holiday": "sukkot", "offset_days": 8})
    assert engine.next_due(t, D(2026, 10, 6)) == D(2027, 10, 24)  # Sukkot 2027 = 16 Oct
    assert engine.next_due(t, D(2026, 9, 30)) == D(2026, 10, 4)


def test_yearly_feb_29_clamps():
    t = task({"type": "yearly", "month": 2, "day": 29, "offset_days": 0})
    assert engine.next_due(t, D(2026, 10, 6)) == D(2027, 2, 28)
    assert engine.next_due(t, D(2027, 3, 1)) == D(2028, 2, 29)


def test_entity_schedule():
    t = task({"type": "entity", "entity_id": "sensor.tami4_filter"})
    assert engine.next_due(t, D(2026, 10, 6), D(2026, 12, 1)) == D(2026, 12, 1)
    assert engine.next_due(t, D(2026, 10, 6), None) is None


def test_project_interval_and_annual():
    t = task({"type": "interval", "every": 3, "unit": "months"}, "2026-09-01")
    assert engine.project(t, D(2026, 1, 1), D(2027, 7, 1), D(2026, 10, 6)) == [
        D(2026, 12, 1), D(2027, 3, 1), D(2027, 6, 1)
    ]
    a = task({"type": "holiday", "holiday": "pesach", "offset_days": 0})
    assert engine.project(a, D(2026, 10, 1), D(2029, 1, 1), D(2026, 10, 6)) == [
        D(2027, 4, 22), D(2028, 4, 11)
    ]


def test_quiet_day():
    assert engine.is_quiet_day(D(2026, 10, 10), False)  # Saturday
    assert engine.is_quiet_day(D(2026, 9, 21), False)  # Yom Kippur (Monday)
    assert not engine.is_quiet_day(D(2026, 10, 6), False)  # Tuesday 25 Tishrei
    assert engine.is_quiet_day(D(2026, 10, 4), True)  # Sunday: Shemini Atzeret day 2 abroad?
    assert not engine.is_quiet_day(D(2026, 10, 4), False)


@pytest.mark.parametrize("key", list(TEMPLATES))
def test_templates_validate(key):
    t = TEMPLATES[key]
    clean = validate_task(
        {"name": t["name"][1], "template": key, "schedule": t["schedule"], "notes": t["note"][1]}, D(2026, 10, 6)
    )
    assert clean["category"] == t["category"]
    assert clean["icon"] == t["icon"]


@pytest.mark.parametrize(
    ("data", "field"),
    [
        ({"name": "", "schedule": {"type": "interval", "every": 1, "unit": "days"}}, "name"),
        ({"name": "x" * 61, "schedule": {"type": "interval", "every": 1, "unit": "days"}}, "name"),
        ({"name": "x", "schedule": {"type": "bogus"}}, "schedule.type"),
        ({"name": "x", "schedule": {"type": "interval", "every": 0, "unit": "days"}}, "schedule.every"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1.5, "unit": "days"}}, "schedule.every"),
        ({"name": "x", "schedule": {"type": "interval", "every": True, "unit": "days"}}, "schedule.every"),
        ({"name": "x", "schedule": {"type": "interval", "every": 21, "unit": "years"}}, "schedule.every"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "decades"}}, "schedule.unit"),
        ({"name": "x", "schedule": {"type": "holiday", "holiday": "xmas"}}, "schedule.holiday"),
        ({"name": "x", "schedule": {"type": "holiday", "holiday": "pesach", "offset_days": 400}}, "schedule.offset_days"),
        ({"name": "x", "schedule": {"type": "yearly", "month": 2, "day": 30}}, "schedule.day"),
        ({"name": "x", "schedule": {"type": "yearly", "month": 13, "day": 1}}, "schedule.month"),
        ({"name": "x", "schedule": {"type": "entity", "entity_id": "light.kitchen"}}, "schedule.entity_id"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "last_done": "2026-10-07"}, "last_done"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "last_done": "garbage"}, "last_done"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "remind_days": -1}, "remind_days"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "icon": "bad icon"}, "icon"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "category": "cars"}, "category"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "template": "nope"}, "template"),
        ({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "days"}, "notes": "n" * 501}, "notes"),
    ],
)
def test_validate_task_errors(data, field):
    with pytest.raises(ValidationError) as err:
        validate_task(data, D(2026, 10, 6))
    assert field in err.value.errors


def test_validate_update_keeps_history_and_snooze_reset_on_schedule_change():
    base = validate_task({"name": "x", "schedule": {"type": "interval", "every": 1, "unit": "months"}}, D(2026, 10, 6))
    base["history"] = [{"date": "2026-10-01"}]
    base["snoozed_until"] = "2026-10-20"
    same = validate_task({"name": "y"}, D(2026, 10, 6), base)
    assert same["id"] == base["id"] and same["history"] == base["history"] and same["snoozed_until"] == "2026-10-20"
    changed = validate_task({"schedule": {"type": "interval", "every": 2, "unit": "months"}}, D(2026, 10, 6), base)
    assert changed["snoozed_until"] is None


def test_validate_completion():
    today = D(2026, 10, 6)
    assert validate_completion({}, today) == (today, "", None)
    assert validate_completion({"date": "2026-10-01", "note": " ok ", "cost": "120.5"}, today) == (D(2026, 10, 1), "ok", 120.5)
    for bad, field in (({"date": "2026-10-07"}, "date"), ({"date": "x"}, "date"), ({"cost": -1}, "cost"), ({"cost": "abc"}, "cost")):
        with pytest.raises(ValidationError) as err:
            validate_completion(bad, today)
        assert field in err.value.errors
