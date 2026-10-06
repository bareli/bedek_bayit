# Changelog

## 0.1.1 (2026-10-06)

- Sidebar icon was blank (`mdi:home-wrench` does not exist); now `mdi:hammer-wrench`. A test checks every icon name against the frontend's icon list.
- `add_task` / `remove_task` services are admin only, like the editor (automations still allowed).

## 0.1.0 (2026-10-06)

First release.

- Household maintenance tasks with "last done / next due": every N days / weeks / months / years, yearly around a Jewish holiday (for example two weeks before Pesach, after Sukkot), yearly on a date, or from a date sensor (for example the Tami4 Edge "filter upcoming replacement" sensor).
- 21 Israeli preset tasks: AC filter and service, Tami4 filter and UV lamp, water bar filter, solar heater (dud shemesh) anode service and collector descaling, smoke detectors, fire extinguisher, mamad filter, earth leakage breaker, gas hose, backflow preventer (mazach), roof and gutters before the rains, chimney, pest control, kitchen and laundry, mezuzot.
- Entities: a next-due date sensor and a "mark done" button per task, a tasks-needing-attention sensor, a to-do list (check off = done) and a calendar of due dates.
- Reminders to notify services: days before, on the day, repeating while overdue; one task gets Done / Snooze buttons on the phone; none on Shabbat and Yom Tov; `bedek_bayit_reminder` and `bedek_bayit_completed` events.
- Completion history with note, cost (₪) and who did it.
- Lovelace card `custom:bedek-bayit-card` and a sidebar page, Hebrew (RTL) and English, with a task editor and a preset picker.
- Services: `complete_task`, `snooze_task`, `add_task`, `remove_task`, `list_tasks`.
