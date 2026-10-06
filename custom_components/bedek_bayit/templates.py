"""Preset Israeli household maintenance tasks.

Intervals are common recommendations (manufacturers, Israeli technicians), not standards:
every one is editable. Each template: category, icon, (en, he) name, (en, he) note, schedule.
"""
from __future__ import annotations

from typing import Any

from .const import SCHED_HOLIDAY, SCHED_INTERVAL, SCHED_YEARLY


def _every(n: int, unit: str) -> dict[str, Any]:
    return {"type": SCHED_INTERVAL, "every": n, "unit": unit}


def _before(holiday: str, days: int) -> dict[str, Any]:
    return {"type": SCHED_HOLIDAY, "holiday": holiday, "offset_days": -days}


def _after(holiday: str, days: int) -> dict[str, Any]:
    return {"type": SCHED_HOLIDAY, "holiday": holiday, "offset_days": days}


def _yearly(month: int, day: int) -> dict[str, Any]:
    return {"type": SCHED_YEARLY, "month": month, "day": day, "offset_days": 0}


TEMPLATES: dict[str, dict[str, Any]] = {
    "ac_filter": {
        "category": "climate",
        "icon": "mdi:air-filter",
        "name": ("AC filter cleaning", "ניקוי פילטר מזגן"),
        "note": (
            "Rinse the indoor unit filters. Every 2 weeks in heavy summer use, every 3 months in light use.",
            "שטיפת הפילטרים ביחידה הפנימית. כל שבועיים בשימוש כבד בקיץ, כל 3 חודשים בשימוש קל.",
        ),
        "schedule": _every(1, "months"),
    },
    "ac_service": {
        "category": "climate",
        "icon": "mdi:air-conditioner",
        "name": ("AC technician service before summer", "שירות טכנאי מזגנים לפני הקיץ"),
        "note": (
            "Deep clean, drain line, gas pressure check.",
            "ניקוי יסודי, צינור ניקוז, בדיקת לחץ גז.",
        ),
        "schedule": _yearly(4, 15),
    },
    "tami4_filter": {
        "category": "water",
        "icon": "mdi:water-check",
        "name": ("Tami4 filter replacement", "החלפת פילטר תמי4"),
        "note": (
            "About every 6 months or 1,500 L. A Tami4 Edge in Home Assistant can drive this task: set the schedule to its 'Filter upcoming replacement' sensor.",
            "בערך כל 6 חודשים או 1,500 ליטר. תמי4 Edge שמחובר ל-Home Assistant יכול לקבוע את המשימה: בחרו בתזמון את החיישן 'Filter upcoming replacement' שלו.",
        ),
        "schedule": _every(6, "months"),
    },
    "tami4_uv": {
        "category": "water",
        "icon": "mdi:lightbulb-fluorescent-tube-outline",
        "name": ("Tami4 UV lamp replacement", "החלפת נורת UV בתמי4"),
        "note": ("Once a year.", "פעם בשנה."),
        "schedule": _every(1, "years"),
    },
    "water_bar_filter": {
        "category": "water",
        "icon": "mdi:cup-water",
        "name": ("Water bar filter (Strauss / other)", "החלפת פילטר בר מים (שטראוס / אחר)"),
        "note": (
            "Check your model's manual; 6 months is a common default.",
            "בדקו בחוברת של הדגם; 6 חודשים הוא ברירת מחדל נפוצה.",
        ),
        "schedule": _every(6, "months"),
    },
    "dud_service": {
        "category": "solar",
        "icon": "mdi:solar-panel",
        "name": ("Solar heater service: magnesium anode", "טיפול בדוד שמש: אנודת מגנזיום"),
        "note": (
            "Replace the anode, clean the mixing valve screens and the tank, new gasket. Most technicians say every 3 years.",
            "החלפת אנודה, ניקוי מסננים בברז הערבוב ושטיפת המיכל, אטם חדש. רוב הטכנאים ממליצים כל 3 שנים.",
        ),
        "schedule": _every(3, "years"),
    },
    "dud_collectors": {
        "category": "solar",
        "icon": "mdi:water-boiler",
        "name": ("Solar collectors descaling", "ניקוי אבנית בקולטים"),
        "note": ("Every 2 to 3 years, more often with hard water.", "כל 2 עד 3 שנים, לעיתים קרובות יותר במים קשים."),
        "schedule": _every(2, "years"),
    },
    "smoke_test": {
        "category": "safety",
        "icon": "mdi:smoke-detector",
        "name": ("Smoke detector test", "בדיקת גלאי עשן"),
        "note": ("Press the test button on every detector.", "לחיצה על כפתור הבדיקה בכל גלאי."),
        "schedule": _every(1, "months"),
    },
    "smoke_battery": {
        "category": "safety",
        "icon": "mdi:battery-alert-variant-outline",
        "name": ("Smoke detector batteries", "החלפת סוללות בגלאי עשן"),
        "note": (
            "Replaceable batteries: once a year. Sealed 10-year units: replace the detector at its expiry date.",
            "סוללות נשלפות: פעם בשנה. גלאים אטומים ל-10 שנים: החלפת הגלאי בתאריך התפוגה.",
        ),
        "schedule": _every(1, "years"),
    },
    "extinguisher": {
        "category": "safety",
        "icon": "mdi:fire-extinguisher",
        "name": ("Fire extinguisher inspection", "בדיקת מטף כיבוי"),
        "note": ("Yearly by a licensed technician (Israeli standard 129).", "פעם בשנה על ידי טכנאי מוסמך (ת\"י 129)."),
        "schedule": _every(1, "years"),
    },
    "mamad_filter": {
        "category": "safety",
        "icon": "mdi:shield-home",
        "name": ("Safe room (mamad) filter check", "בדיקת מערכת הסינון בממ\"ד"),
        "note": (
            "Check the ventilation system works and the filter's printed expiry date. See oref.org.il.",
            "בדיקה שמערכת האוורור עובדת ושהמסנן בתוקף (תאריך מודפס). פרטים באתר פיקוד העורף.",
        ),
        "schedule": _every(1, "years"),
    },
    "rcd_test": {
        "category": "safety",
        "icon": "mdi:flash-alert",
        "name": ("Earth leakage breaker (pachat) test", "בדיקת מפסק פחת"),
        "note": ("Press the T button on the breaker; power should cut.", "לחיצה על כפתור T במפסק; החשמל אמור להיפסק."),
        "schedule": _every(6, "months"),
    },
    "gas_hose": {
        "category": "gas",
        "icon": "mdi:gas-cylinder",
        "name": ("Gas hose replacement", "החלפת צינור גז"),
        "note": (
            "Rubber hose every 5 years, with the supplier's periodic inspection.",
            "צינור גומי כל 5 שנים, יחד עם הבדיקה התקופתית של ספק הגז.",
        ),
        "schedule": _every(5, "years"),
    },
    "backflow": {
        "category": "water",
        "icon": "mdi:pipe-valve",
        "name": ("Backflow preventer (mazach) test", "בדיקת מז\"ח"),
        "note": ("Yearly test by a certified tester, where installed.", "בדיקה שנתית על ידי בודק מוסמך, היכן שמותקן."),
        "schedule": _every(1, "years"),
    },
    "roof_sealing": {
        "category": "structure",
        "icon": "mdi:home-roof",
        "name": ("Roof and gutters before the rains", "גג ומרזבים לפני הגשמים"),
        "note": ("Clear gutters and drains, check the roof sealing.", "ניקוי מרזבים וניקוזים, בדיקת איטום הגג."),
        "schedule": _after("sukkot", 8),
    },
    "chimney": {
        "category": "structure",
        "icon": "mdi:fireplace",
        "name": ("Chimney cleaning", "ניקוי ארובה"),
        "note": ("After the heating season, with the Pesach cleaning.", "בסוף עונת החימום, יחד עם ניקיון הפסח."),
        "schedule": _before("pesach", 14),
    },
    "pest_control": {
        "category": "structure",
        "icon": "mdi:bug-outline",
        "name": ("Pest control", "הדברה"),
        "note": ("Before summer.", "לפני הקיץ."),
        "schedule": _yearly(4, 1),
    },
    "washing_machine": {
        "category": "kitchen",
        "icon": "mdi:washing-machine",
        "name": ("Washing machine drum and filter", "ניקוי תוף ומסנן במכונת כביסה"),
        "note": ("Hot empty cycle, clean the pump filter.", "הפעלה ריקה בחום, ניקוי מסנן המשאבה."),
        "schedule": _every(1, "months"),
    },
    "dishwasher_filter": {
        "category": "kitchen",
        "icon": "mdi:dishwasher",
        "name": ("Dishwasher filter cleaning", "ניקוי מסנן במדיח"),
        "note": ("", ""),
        "schedule": _every(1, "months"),
    },
    "fridge_coils": {
        "category": "kitchen",
        "icon": "mdi:fridge-outline",
        "name": ("Fridge coils and seals", "ניקוי סלילי מקרר ובדיקת גומיות"),
        "note": ("", ""),
        "schedule": _every(1, "years"),
    },
    "mezuzot": {
        "category": "religious",
        "icon": "mdi:script-text-outline",
        "name": ("Mezuzot check", "בדיקת מזוזות"),
        "note": ("Twice in seven years (every 3.5 years).", "פעמיים בשבע שנים (כל שלוש וחצי שנים)."),
        "schedule": _every(42, "months"),
    },
}

# Offered pre-selected in the setup step.
DEFAULT_TEMPLATES = ["ac_filter", "tami4_filter", "dud_service", "smoke_test", "gas_hose", "chimney"]


def template_view(key: str, lang: str) -> dict[str, Any]:
    """Catalog entry for the frontend in one language."""
    t = TEMPLATES[key]
    i = 1 if lang == "he" else 0
    return {
        "key": key,
        "category": t["category"],
        "icon": t["icon"],
        "name": t["name"][i],
        "notes": t["note"][i],
        "schedule": dict(t["schedule"]),
    }
