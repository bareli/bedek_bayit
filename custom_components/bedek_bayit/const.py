"""Constants for Bedek Bayit (no Home Assistant imports: the engine uses them)."""
from __future__ import annotations

DOMAIN = "bedek_bayit"

# Options
CONF_NOTIFY_TARGETS = "notify_targets"
CONF_REMINDER_TIME = "reminder_time"
CONF_REMIND_DAYS = "remind_days"
CONF_REPEAT_DAYS = "repeat_days"
CONF_SNOOZE_DAYS = "snooze_days"
CONF_QUIET_ON_SHABBAT = "quiet_on_shabbat"
CONF_DIASPORA = "diaspora"
CONF_LANGUAGE = "language"
CONF_TEMPLATES = "templates"

DEFAULT_REMINDER_TIME = "09:00"
DEFAULT_REMIND_DAYS = 7
DEFAULT_REPEAT_DAYS = 3
DEFAULT_SNOOZE_DAYS = 7
MAX_DAYS = 365

LANG_AUTO = "auto"
LANGUAGES = [LANG_AUTO, "he", "en"]

# Schedule types
SCHED_INTERVAL = "interval"
SCHED_HOLIDAY = "holiday"
SCHED_YEARLY = "yearly"
SCHED_ENTITY = "entity"
SCHEDULE_TYPES = [SCHED_INTERVAL, SCHED_HOLIDAY, SCHED_YEARLY, SCHED_ENTITY]

UNITS = ["days", "weeks", "months", "years"]
MAX_EVERY = {"days": 3650, "weeks": 520, "months": 240, "years": 20}

HOLIDAYS = ["rosh_hashana", "sukkot", "hanukkah", "purim", "pesach", "shavuot"]
# A completion this many days before an annual (holiday / yearly) due date counts for it.
ANNUAL_WINDOW_DAYS = 90
MAX_OFFSET_DAYS = 180

CATEGORIES = ["climate", "water", "solar", "safety", "gas", "kitchen", "structure", "religious", "general"]

# Status, most urgent first
ST_OVERDUE = "overdue"
ST_DUE = "due"
ST_SOON = "due_soon"
ST_OK = "ok"
ST_UNKNOWN = "unknown"
ST_PAUSED = "paused"
STATUSES = [ST_OVERDUE, ST_DUE, ST_SOON, ST_OK, ST_UNKNOWN, ST_PAUSED]
ATTENTION = (ST_OVERDUE, ST_DUE, ST_SOON)

MAX_TASKS = 200
MAX_HISTORY = 50
MAX_NAME = 60
MAX_NOTES = 500
MAX_COST = 1_000_000

SIGNAL_UPDATED = f"{DOMAIN}_updated"
SIGNAL_TASK_ADDED = f"{DOMAIN}_task_added"
EVENT_REMINDER = f"{DOMAIN}_reminder"
EVENT_COMPLETED = f"{DOMAIN}_completed"

ACTION_PREFIX = "BEDEK_BAYIT_"
ACTION_DONE = "DONE"
ACTION_SNOOZE = "SNOOZE"

PANEL_URL_PATH = "bedek-bayit"
