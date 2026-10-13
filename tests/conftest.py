"""Shared fixtures for Bedek Bayit tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bedek_bayit.config_flow import OPTION_DEFAULTS
from custom_components.bedek_bayit.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def no_frontend():
    """Lovelace resource and sidebar panel need the real frontend; not under test."""
    with patch("custom_components.bedek_bayit._async_register_card", return_value=None), patch(
        "custom_components.bedek_bayit._async_register_panel", return_value=None
    ):
        yield


@pytest.fixture(autouse=True)
async def israel(hass: HomeAssistant):
    await hass.config.async_update(time_zone="Asia/Jerusalem", country="IL", language="en")
    yield


def make_entry(hass: HomeAssistant, templates: list[str] | None = None, **options) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedek Bayit",
        data={"templates": templates or []},
        options={**OPTION_DEFAULTS, **options},
    )
    entry.add_to_hass(hass)
    return entry


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


async def setup_deps(hass: HomeAssistant) -> None:
    """Load manifest dependencies before the WS client starts http (router freezes then)."""
    for domain in ("frontend", "lovelace", "panel_custom"):
        assert await async_setup_component(hass, domain, {})
