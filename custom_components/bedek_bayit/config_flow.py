"""Config flow (single instance) and options."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_DIASPORA,
    CONF_LANGUAGE,
    CONF_NOTIFY_TARGETS,
    CONF_QUIET_ON_SHABBAT,
    CONF_REMIND_DAYS,
    CONF_REMINDER_TIME,
    CONF_REPEAT_DAYS,
    CONF_SNOOZE_DAYS,
    CONF_TEMPLATES,
    DEFAULT_REMIND_DAYS,
    DEFAULT_REMINDER_TIME,
    DEFAULT_REPEAT_DAYS,
    DEFAULT_SNOOZE_DAYS,
    DOMAIN,
    LANG_AUTO,
    LANGUAGES,
    MAX_DAYS,
)
from .templates import DEFAULT_TEMPLATES, TEMPLATES

OPTION_DEFAULTS: dict[str, Any] = {
    CONF_NOTIFY_TARGETS: [],
    CONF_REMINDER_TIME: DEFAULT_REMINDER_TIME,
    CONF_REMIND_DAYS: DEFAULT_REMIND_DAYS,
    CONF_REPEAT_DAYS: DEFAULT_REPEAT_DAYS,
    CONF_SNOOZE_DAYS: DEFAULT_SNOOZE_DAYS,
    CONF_QUIET_ON_SHABBAT: True,
    CONF_DIASPORA: False,
    CONF_LANGUAGE: LANG_AUTO,
}


def notify_targets(hass: HomeAssistant) -> list[str]:
    return sorted(f"notify.{name}" for name in hass.services.async_services_for_domain("notify"))


def _days(low: int) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=low, max=MAX_DAYS, step=1, mode=selector.NumberSelectorMode.BOX)
    )


def options_schema(hass: HomeAssistant, current: dict[str, Any]) -> vol.Schema:
    c = {**OPTION_DEFAULTS, **current}
    targets = sorted(set(notify_targets(hass)) | set(c[CONF_NOTIFY_TARGETS]))
    return vol.Schema(
        {
            vol.Optional(CONF_NOTIFY_TARGETS, default=c[CONF_NOTIFY_TARGETS]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=targets, multiple=True, custom_value=True)
            ),
            vol.Required(CONF_REMINDER_TIME, default=c[CONF_REMINDER_TIME]): selector.TimeSelector(),
            vol.Required(CONF_REMIND_DAYS, default=c[CONF_REMIND_DAYS]): _days(0),
            vol.Required(CONF_REPEAT_DAYS, default=c[CONF_REPEAT_DAYS]): _days(0),
            vol.Required(CONF_SNOOZE_DAYS, default=c[CONF_SNOOZE_DAYS]): _days(1),
            vol.Required(CONF_QUIET_ON_SHABBAT, default=c[CONF_QUIET_ON_SHABBAT]): selector.BooleanSelector(),
            vol.Required(CONF_DIASPORA, default=c[CONF_DIASPORA]): selector.BooleanSelector(),
            vol.Required(CONF_LANGUAGE, default=c[CONF_LANGUAGE]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=LANGUAGES, translation_key=CONF_LANGUAGE)
            ),
        }
    )


def validate_options(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Server-side validation (selectors are a UX aid, not a guarantee)."""
    errors: dict[str, str] = {}
    out = dict(data)
    for key, low in ((CONF_REMIND_DAYS, 0), (CONF_REPEAT_DAYS, 0), (CONF_SNOOZE_DAYS, 1)):
        try:
            value = float(data.get(key, OPTION_DEFAULTS[key]))
        except (TypeError, ValueError):
            errors[key] = "invalid_days"
            continue
        if value != int(value) or not low <= value <= MAX_DAYS:
            errors[key] = "invalid_days"
        else:
            out[key] = int(value)
    time = str(data.get(CONF_REMINDER_TIME, ""))
    parts = time.split(":")
    try:
        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
        out[CONF_REMINDER_TIME] = f"{hours:02d}:{minutes:02d}"
    except (IndexError, ValueError):
        errors[CONF_REMINDER_TIME] = "invalid_time"
    targets = data.get(CONF_NOTIFY_TARGETS) or []
    if not isinstance(targets, list) or any(
        not isinstance(t, str) or not t.startswith("notify.") or len(t) <= 7 for t in targets
    ):
        errors[CONF_NOTIFY_TARGETS] = "invalid_target"
    if data.get(CONF_LANGUAGE, LANG_AUTO) not in LANGUAGES:
        errors[CONF_LANGUAGE] = "invalid"
    return out, errors


class BedekBayitConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors: dict[str, str] = {}
        if user_input is not None:
            templates = user_input.get(CONF_TEMPLATES) or []
            if any(t not in TEMPLATES for t in templates):
                errors[CONF_TEMPLATES] = "invalid"
            else:
                title = "בדק בית" if str(self.hass.config.language or "").startswith("he") else "Bedek Bayit"
                return self.async_create_entry(
                    title=title, data={CONF_TEMPLATES: templates}, options=dict(OPTION_DEFAULTS)
                )
        schema = vol.Schema(
            {
                vol.Optional(CONF_TEMPLATES, default=DEFAULT_TEMPLATES): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=list(TEMPLATES), multiple=True, translation_key=CONF_TEMPLATES
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return BedekBayitOptionsFlow()


class BedekBayitOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        current = {**OPTION_DEFAULTS, **self.config_entry.options}
        if user_input is not None:
            clean, errors = validate_options({**current, **user_input})
            if not errors:
                return self.async_create_entry(data=clean)
            current = {**current, **user_input}
        return self.async_show_form(
            step_id="init", data_schema=options_schema(self.hass, current), errors=errors
        )
