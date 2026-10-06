"""Pure scheduling logic: next due date, status, projections (no Home Assistant imports)."""
from __future__ import annotations

import calendar
import datetime as dt
from functools import lru_cache
from typing import Any, Iterator

from hdate import HDateInfo
from hdate.hebrew_date import HebrewDate, Months

from .const import (
    ANNUAL_WINDOW_DAYS,
    SCHED_ENTITY,
    SCHED_HOLIDAY,
    SCHED_INTERVAL,
    SCHED_YEARLY,
    ST_DUE,
    ST_OK,
    ST_OVERDUE,
    ST_PAUSED,
    ST_SOON,
    ST_UNKNOWN,
)

# Hebrew month and day of each anchor holiday (first day).
_HOLIDAY_DAY: dict[str, tuple[Months | None, int]] = {
    "rosh_hashana": (Months.TISHREI, 1),
    "sukkot": (Months.TISHREI, 15),
    "hanukkah": (Months.KISLEV, 25),
    "purim": (None, 14),  # Adar, or Adar II in a leap year
    "pesach": (Months.NISAN, 15),
    "shavuot": (Months.SIVAN, 6),
}


def parse_date(value: Any) -> dt.date | None:
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def add_months(day: dt.date, months: int) -> dt.date:
    """Calendar months; the day clamps to the end of a shorter month (31 Jan + 1 = 28/29 Feb)."""
    total = day.year * 12 + day.month - 1 + months
    year, month = divmod(total, 12)
    month += 1
    return dt.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def add_interval(day: dt.date, every: int, unit: str) -> dt.date:
    if unit == "days":
        return day + dt.timedelta(days=every)
    if unit == "weeks":
        return day + dt.timedelta(weeks=every)
    if unit == "months":
        return add_months(day, every)
    if unit == "years":
        return add_months(day, every * 12)
    raise ValueError(f"unknown unit {unit}")


@lru_cache(maxsize=512)
def holiday_date(holiday: str, hebrew_year: int) -> dt.date:
    month, day = _HOLIDAY_DAY[holiday]
    if month is None:
        month = Months.ADAR_II if HebrewDate(hebrew_year, Months.TISHREI, 1).is_leap_year() else Months.ADAR
    return HebrewDate(hebrew_year, month, day).to_gdate()


def annual_dates(schedule: dict[str, Any], start_year_day: dt.date) -> Iterator[dt.date]:
    """Due dates of an annual schedule (holiday or fixed date, plus offset) in ascending order,
    starting from about a year before start_year_day."""
    offset = dt.timedelta(days=int(schedule.get("offset_days") or 0))
    if schedule["type"] == SCHED_HOLIDAY:
        year = HebrewDate.from_gdate(start_year_day).year - 2
        while True:
            yield holiday_date(schedule["holiday"], year) + offset
            year += 1
    else:
        month, day = int(schedule["month"]), int(schedule["day"])
        year = start_year_day.year - 2
        while True:
            yield dt.date(year, month, min(day, calendar.monthrange(year, month)[1])) + offset
            year += 1


def annual_after(schedule: dict[str, Any], last_done: dt.date | None, today: dt.date) -> dt.date:
    """Next annual due date not yet covered by last_done.

    A completion up to ANNUAL_WINDOW_DAYS before a due date (or any time after it) covers it.
    Never done: the next due date from today.
    """
    if last_done is None:
        return next(d for d in annual_dates(schedule, today) if d >= today)
    return next(d for d in annual_dates(schedule, last_done) if d - dt.timedelta(days=ANNUAL_WINDOW_DAYS) > last_done)


def base_due(task: dict[str, Any], today: dt.date, entity_due: dt.date | None = None) -> dt.date | None:
    """Due date from the schedule alone (no snooze). None = unknown (never done / no data)."""
    schedule = task["schedule"]
    kind = schedule["type"]
    last_done = parse_date(task.get("last_done"))
    if kind == SCHED_INTERVAL:
        if last_done is None:
            return None
        return add_interval(last_done, int(schedule["every"]), schedule["unit"])
    if kind in (SCHED_HOLIDAY, SCHED_YEARLY):
        return annual_after(schedule, last_done, today)
    if kind == SCHED_ENTITY:
        return entity_due
    raise ValueError(f"unknown schedule {kind}")


def next_due(task: dict[str, Any], today: dt.date, entity_due: dt.date | None = None) -> dt.date | None:
    due = base_due(task, today, entity_due)
    snoozed = parse_date(task.get("snoozed_until"))
    if due is not None and snoozed is not None and snoozed > due:
        return snoozed
    return due


def status(task: dict[str, Any], due: dt.date | None, today: dt.date, remind_days: int) -> str:
    if task.get("paused"):
        return ST_PAUSED
    if due is None:
        return ST_UNKNOWN
    days = (due - today).days
    if days < 0:
        return ST_OVERDUE
    if days == 0:
        return ST_DUE
    if days <= remind_days:
        return ST_SOON
    return ST_OK


def progress(task: dict[str, Any], due: dt.date | None, today: dt.date) -> float | None:
    """Share of the cycle elapsed since the last completion (0..1, capped)."""
    last_done = parse_date(task.get("last_done"))
    if due is None or last_done is None or due <= last_done:
        return None
    return round(min(max((today - last_done).days / (due - last_done).days, 0.0), 1.0), 3)


def project(
    task: dict[str, Any], start: dt.date, end: dt.date, today: dt.date, entity_due: dt.date | None = None, limit: int = 60
) -> list[dt.date]:
    """Due dates in [start, end): the next one, then later ones assuming each is done on time."""
    if task.get("paused"):
        return []
    due = next_due(task, today, entity_due)
    if due is None:
        return []
    schedule = task["schedule"]
    out: list[dt.date] = []
    while due < end and len(out) < limit:
        if due >= start:
            out.append(due)
        if schedule["type"] == SCHED_INTERVAL:
            due = add_interval(due, int(schedule["every"]), schedule["unit"])
        elif schedule["type"] in (SCHED_HOLIDAY, SCHED_YEARLY):
            due = annual_after(schedule, due, today)
        else:
            break
    return out


def is_quiet_day(day: dt.date, diaspora: bool) -> bool:
    """Shabbat or Yom Tov (date level)."""
    if day.weekday() == 5:
        return True
    return bool(HDateInfo(day, diaspora=diaspora).is_yom_tov)
