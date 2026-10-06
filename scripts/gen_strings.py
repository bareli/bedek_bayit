"""Generate strings.json, translations/en.json and translations/he.json from one table.

Run from the repo root: python scripts/gen_strings.py
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "custom_components", "bedek_bayit")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"bb_{name}", os.path.join(ROOT, f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


const = _load("const")
_src = open(os.path.join(ROOT, "templates.py"), encoding="utf-8").read().replace("from .const import", "from bb_const import")
templates = type(sys)("bb_templates")
exec(compile(_src, "templates.py", "exec"), templates.__dict__)

OPTION_FIELDS = {
    "notify_targets": ("Send reminders to", "לשלוח תזכורות אל"),
    "reminder_time": ("Reminder time", "שעת התזכורת"),
    "remind_days": ("Start reminding, days before due", "להתחיל להזכיר, ימים לפני המועד"),
    "repeat_days": ("Repeat overdue reminders every (days, 0 = once)", "לחזור על תזכורת באיחור כל (ימים, 0 = פעם אחת)"),
    "snooze_days": ("Snooze length (days)", "משך דחייה (ימים)"),
    "quiet_on_shabbat": ("No reminders on Shabbat and Yom Tov", "בלי תזכורות בשבת ובחג"),
    "diaspora": ("Diaspora (two-day Yom Tov)", "חוץ לארץ (יום טוב שני)"),
    "language": ("Language for notifications and task names", "שפת ההתראות ושמות המשימות"),
}
OPTION_DESCRIPTIONS = {
    "notify_targets": (
        "For example your phone. With one task, the phone shows Done / Snooze buttons. Automations can also use the bedek_bayit_reminder event.",
        "למשל הטלפון שלך. כשמדובר במשימה אחת, בטלפון יופיעו הכפתורים בוצע / דחייה. אוטומציות יכולות להשתמש גם באירוע bedek_bayit_reminder.",
    ),
    "remind_days": ("Each task can override this.", "אפשר לשנות לכל משימה בנפרד."),
    "quiet_on_shabbat": (
        "A reminder that falls on Shabbat or Yom Tov is sent the next weekday.",
        "תזכורת שחלה בשבת או בחג תישלח ביום החול הבא.",
    ),
}
ERRORS = {
    "invalid_days": ("Whole number of days, 0 to 365 (snooze: 1 to 365).", "מספר שלם של ימים, 0 עד 365 (דחייה: 1 עד 365)."),
    "invalid_time": ("Use HH:MM.", "יש להזין בפורמט HH:MM."),
    "invalid_target": ("Each target must be a notify service, for example notify.mobile_app_phone.", "כל יעד חייב להיות שירות notify, למשל notify.mobile_app_phone."),
    "invalid": ("Invalid value.", "ערך לא תקין."),
}
SELECTORS = {
    "language": {"auto": ("Home Assistant language", "שפת Home Assistant"), "he": ("Hebrew", "עברית"), "en": ("English", "אנגלית")},
    "category": {
        "climate": ("Air conditioning", "מיזוג אוויר"),
        "water": ("Water", "מים"),
        "solar": ("Solar water heater", "דוד שמש"),
        "safety": ("Safety", "בטיחות"),
        "gas": ("Gas", "גז"),
        "kitchen": ("Kitchen and laundry", "מטבח וכביסה"),
        "structure": ("House and roof", "מבנה וגג"),
        "religious": ("Judaica", "יהדות"),
        "general": ("General", "כללי"),
    },
    "schedule_type": {
        "interval": ("Every N days / weeks / months / years", "כל X ימים / שבועות / חודשים / שנים"),
        "holiday": ("Yearly, around a Jewish holiday", "שנתי, סביב חג"),
        "yearly": ("Yearly, on a date", "שנתי, בתאריך"),
        "entity": ("From a sensor (for example Tami4)", "לפי חיישן (למשל תמי4)"),
    },
    "unit": {"days": ("Days", "ימים"), "weeks": ("Weeks", "שבועות"), "months": ("Months", "חודשים"), "years": ("Years", "שנים")},
    "holiday": {
        "rosh_hashana": ("Rosh Hashana", "ראש השנה"),
        "sukkot": ("Sukkot", "סוכות"),
        "hanukkah": ("Hanukkah", "חנוכה"),
        "purim": ("Purim", "פורים"),
        "pesach": ("Pesach", "פסח"),
        "shavuot": ("Shavuot", "שבועות"),
    },
    "templates": {k: v["name"] for k, v in templates.TEMPLATES.items()},
}
ENTITIES = {
    "sensor": {"attention": ("Tasks needing attention", "משימות שדורשות טיפול")},
    "todo": {"maintenance": ("Home maintenance", "תחזוקת הבית")},
    "calendar": {"maintenance": ("Home maintenance", "תחזוקת הבית")},
}
TARGET_FIELDS = {
    "task_id": (("Task ID", "מזהה משימה"), ("From list_tasks or a sensor's task_id attribute.", "מתוך list_tasks או מהמאפיין task_id של החיישן.")),
    "entity_id": (("Task entity", "ישות המשימה"), ("The task's sensor or button (instead of task_id).", "החיישן או הכפתור של המשימה (במקום task_id).")),
}
SERVICES = {
    "complete_task": (
        ("Mark task done", "סימון משימה כבוצעה"),
        ("Records a completion and moves the next due date.", "רושם ביצוע ומעדכן את המועד הבא."),
        {
            **TARGET_FIELDS,
            "date": (("Date", "תאריך"), ("Default: today.", "ברירת מחדל: היום.")),
            "note": (("Note", "הערה"), ("", "")),
            "cost": (("Cost (₪)", "עלות (₪)"), ("", "")),
        },
    ),
    "snooze_task": (
        ("Snooze task", "דחיית משימה"),
        ("Pushes the due date; cleared when the task is done.", "דוחה את המועד; מתבטל כשהמשימה מבוצעת."),
        {**TARGET_FIELDS, "days": (("Days", "ימים"), ("Default: the snooze length option.", "ברירת מחדל: משך הדחייה בהגדרות."))},
    ),
    "remove_task": (("Remove task", "מחיקת משימה"), ("Deletes the task and its entities.", "מוחק את המשימה ואת הישויות שלה."), TARGET_FIELDS),
    "add_task": (
        ("Add task", "הוספת משימה"),
        ("Creates a maintenance task.", "יוצר משימת תחזוקה."),
        {
            "name": (("Name", "שם"), ("", "")),
            "template": (("Template", "תבנית"), ("Optional preset key, for example ac_filter.", "מפתח תבנית אופציונלי, למשל ac_filter.")),
            "category": (("Category", "קטגוריה"), ("", "")),
            "icon": (("Icon", "סמל"), ("", "")),
            "schedule_type": (("Schedule", "תזמון"), ("", "")),
            "every": (("Every", "כל"), ("For a recurring schedule.", "לתזמון חוזר.")),
            "unit": (("Unit", "יחידה"), ("", "")),
            "holiday": (("Holiday", "חג"), ("", "")),
            "month": (("Month", "חודש"), ("For a yearly date.", "לתאריך שנתי.")),
            "day": (("Day", "יום"), ("", "")),
            "offset_days": (("Days from the date", "ימים מהתאריך"), ("Negative = before (for example -14 = two weeks before Pesach).", "שלילי = לפני (למשל 14- = שבועיים לפני פסח).")),
            "source_entity": (("Due date sensor", "חיישן מועד"), ("A date or timestamp sensor, for example Tami4 filter upcoming replacement.", "חיישן תאריך או זמן, למשל מועד החלפת הפילטר של תמי4.")),
            "last_done": (("Last done", "בוצע לאחרונה"), ("", "")),
            "remind_days": (("Remind days before", "להזכיר ימים לפני"), ("", "")),
            "notes": (("Notes", "הערות"), ("", "")),
        },
    ),
    "list_tasks": (("List tasks", "רשימת משימות"), ("Returns all tasks with their status and due date.", "מחזיר את כל המשימות עם הסטטוס והמועד."), {}),
}


def build(i):
    def pick(pair):
        return pair[i]

    options_data = {k: pick(v) for k, v in OPTION_FIELDS.items()}
    return {
        "config": {
            "step": {
                "user": {
                    "title": pick(("Bedek Bayit", "בדק בית")),
                    "description": pick((
                        "Household maintenance tracker. Pick starter tasks (you can add, edit or remove tasks later in the Bedek Bayit sidebar page). Intervals are common recommendations; check your manuals.",
                        "מעקב תחזוקת הבית. בחרו משימות להתחלה (אפשר להוסיף, לערוך ולמחוק בהמשך בדף בדק בית בסרגל הצד). התדירויות הן המלצות נפוצות; כדאי לבדוק בחוברות ההוראות.",
                    )),
                    "data": {"templates": pick(("Starter tasks", "משימות להתחלה"))},
                }
            },
            "error": {k: pick(v) for k, v in ERRORS.items()},
            "abort": {"single_instance_allowed": pick(("Bedek Bayit is already set up.", "בדק בית כבר מוגדר."))},
        },
        "options": {
            "step": {
                "init": {
                    "title": pick(("Reminders", "תזכורות")),
                    "data": options_data,
                    "data_description": {k: pick(v) for k, v in OPTION_DESCRIPTIONS.items()},
                }
            },
            "error": {k: pick(v) for k, v in ERRORS.items()},
        },
        "selector": {
            key: {"options": {k: pick(v) for k, v in opts.items()}} for key, opts in SELECTORS.items()
        },
        "entity": {
            platform: {key: {"name": pick(v)} for key, v in names.items()} for platform, names in ENTITIES.items()
        },
        "services": {
            svc: {
                "name": pick(name),
                "description": pick(desc),
                "fields": {f: {"name": pick(n), "description": pick(d)} for f, (n, d) in fields.items()},
            }
            for svc, (name, desc, fields) in SERVICES.items()
        },
    }


def write(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    en, he = build(0), build(1)
    write(os.path.join(ROOT, "strings.json"), en)
    write(os.path.join(ROOT, "translations", "en.json"), en)
    write(os.path.join(ROOT, "translations", "he.json"), he)
