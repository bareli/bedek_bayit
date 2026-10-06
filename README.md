# Bedek Bayit (בדק בית)

Household maintenance tracker for Home Assistant, Israel flavor. It tracks when each job was last done and when it is next due, sends reminders, and comes with a Hebrew (RTL) and English card.

[עברית למטה](#עברית)

- **Israeli presets**: AC filter, Tami4 filter and UV lamp, Strauss or other water bar filters, solar water heater (dud shemesh) anode service, smoke detectors, gas hose, mamad filter, backflow preventer (mazach), roof and gutters before the rains, chimney cleaning before Pesach, mezuzot, and more (21 in all).
- **Schedules that fit Israeli life**:
  - every N days, weeks, months or years
  - **yearly around a Jewish holiday** (for example two weeks before Pesach, or a week after Sukkot), from the Hebrew calendar
  - yearly on a fixed date (for example AC service before summer)
  - **from a sensor**: the Tami4 Edge integration's "filter upcoming replacement" sensor can set the due date
- **Reminders**: a set number of days before the due date, on the day, and every few days while it is overdue. A phone notification for a single task has **Done** and **Snooze** buttons. **No reminders on Shabbat or Yom Tov**; they go out the next weekday.
- **History**: every completion is recorded with its date, a note, the cost in ₪, and who did it.
- **Entities for automations**: per task, a next-due date sensor and a "mark done" button. Also a tasks-needing-attention count, a to-do list (checking an item off marks the task done), and a calendar of upcoming due dates.
- **Card and sidebar page**: everything you need is on the card: a status for each task, a progress bar, one-tap **Done**, snooze, edit, history, and a preset picker.

## Install

HACS → three dots → Custom repositories → `https://github.com/bareli/bedek_bayit` (Integration) → install → restart Home Assistant.
Then go to Settings → Devices & services → Add integration → **Bedek Bayit**, and pick your starter tasks.

The card resource is registered automatically on dashboards in storage mode. For YAML-mode dashboards, add `/bedek_bayit_static/card.js` as a JavaScript module resource yourself.

## Card

```yaml
type: custom:bedek-bayit-card
title: Home maintenance       # optional
attention_only: false         # true = only overdue / today / soon
limit: 0                      # 0 = all
categories: [climate, water]  # optional filter
show_add: true                # Add button (admins)
```

Everyone in the household can mark tasks done or snooze them. Only admins can add, edit or delete tasks.

## How due dates work

| Schedule | Next due |
|---|---|
| Every N units | last done + N (31 Jan + 1 month = 28/29 Feb) |
| Around a holiday | the next holiday date plus the offset. A completion up to 90 days before a due date counts for it. Never done: the next occurrence |
| Yearly on a date | same rule as a holiday (29 Feb = 28 Feb in common years) |
| From a sensor | the sensor's date or timestamp |

Status: `overdue`, `due` (today), `due_soon` (within the reminder window, default 7 days), `ok`, `unknown` (never done, or no sensor data), `paused`. Snoozing only moves the due date later, and it is cleared when the task is done.

## Services

| Service | What it does |
|---|---|
| `bedek_bayit.complete_task` | `task_id` or `entity_id`; optional `date`, `note`, `cost` |
| `bedek_bayit.snooze_task` | `task_id` or `entity_id`; optional `days` |
| `bedek_bayit.add_task` | name + schedule fields; returns `task_id` |
| `bedek_bayit.remove_task` | `task_id` or `entity_id` |
| `bedek_bayit.list_tasks` | returns all tasks with status and due date |

Events: `bedek_bayit_reminder` (`task_id`, `name`, `status`, `due`, `days_left`, `message`) and `bedek_bayit_completed`.

Example: mark the AC filter done from an NFC tag.

```yaml
triggers:
  - trigger: tag
    tag_id: ac-filter
actions:
  - action: bedek_bayit.complete_task
    data:
      entity_id: sensor.bedek_bayit_ac_filter
```

## Options

Notification targets, reminder time (default 09:00), days before the due date to start reminding (7), how often to repeat overdue reminders (every 3 days), snooze length (7 days), no reminders on Shabbat and Yom Tov (on), diaspora two-day Yom Tov (off), and language.

The preset intervals are common recommendations from manufacturers and Israeli technicians, not official standards. Check your manuals and edit any task.

---

## עברית

**בדק בית** עוקב אחרי תחזוקת הבית: מתי כל דבר בוצע לאחרונה ומתי צריך לבצע אותו שוב, עם תזכורות וכרטיס בעברית.

- **משימות מוכנות**: פילטר מזגן, פילטר תמי4 ונורת UV, בר מים, אנודה בדוד שמש, גלאי עשן, צינור גז, מסנן ממ"ד, מז"ח, גג ומרזבים לפני הגשמים, ניקוי ארובה לפני פסח, בדיקת מזוזות ועוד.
- **תזמונים**:
  - כל X ימים, שבועות, חודשים או שנים
  - שנתי סביב חג (למשל שבועיים לפני פסח), לפי הלוח העברי
  - שנתי בתאריך קבוע
  - לפי חיישן (למשל מועד החלפת הפילטר מאינטגרציית תמי4)
- **תזכורות**: כמה ימים לפני המועד, ביום עצמו, ושוב כל כמה ימים כשהמשימה באיחור. בטלפון מופיעים הכפתורים "בוצע" ו"דחייה". **בלי תזכורות בשבת ובחג.**
- **היסטוריה**: לכל ביצוע נשמרים תאריך, הערה, עלות בשקלים ומי ביצע.
- **ישויות**: חיישן מועד וכפתור "סמן כבוצע" לכל משימה, וגם רשימת מטלות ולוח שנה.
- **כרטיס ודף בסרגל הצד**: בעברית מימין לשמאל. כל בני הבית יכולים לסמן משימה כבוצעה, ורק מנהלים יכולים לערוך.

התדירויות המוצעות הן המלצות נפוצות של יצרנים וטכנאים, לא תקן רשמי. כדאי לבדוק בחוברות ההוראות ולערוך לפי הצורך.

## License

MIT
