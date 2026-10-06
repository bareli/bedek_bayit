"""Repository conventions: generated strings in sync, frontend hygiene, manifest/hacs consistency."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "bedek_bayit"


def _gen():
    spec = importlib.util.spec_from_file_location("gen_strings", ROOT / "scripts" / "gen_strings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_strings_generated_and_in_sync():
    gen = _gen()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))  # noqa: E731
    assert load(COMP / "strings.json") == gen.build(0)
    assert load(COMP / "translations" / "en.json") == gen.build(0)
    assert load(COMP / "translations" / "he.json") == gen.build(1)


def test_services_have_strings():
    services = yaml.safe_load((COMP / "services.yaml").read_text(encoding="utf-8"))
    strings = json.loads((COMP / "strings.json").read_text(encoding="utf-8"))["services"]
    assert set(services) == set(strings)
    for name, spec in services.items():
        assert set((spec or {}).get("fields", {})) == set(strings[name]["fields"]), name


def test_frontend_hygiene():
    for path in (COMP / "www").glob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\bconsole\.", text), path.name
        assert "innerHTML" not in text, path.name
        # bidi isolates only as escapes, never literal invisible characters
        assert not re.search("[\u2066-\u2069\u200e\u200f]", text), path.name


def test_versions_and_min_ha():
    manifest = json.loads((COMP / "manifest.json").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## {manifest['version']}" in changelog
    assert json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))["homeassistant"]


def test_icons_exist():
    """Every mdi icon we reference exists in the installed frontend (an unknown name renders blank)."""
    import pytest

    hass_frontend = pytest.importorskip("hass_frontend")
    icon_list = Path(hass_frontend.__file__).parent / "static" / "mdi" / "iconList.json"
    names = {i["name"] if isinstance(i, dict) else i for i in json.loads(icon_list.read_text(encoding="utf-8"))}
    used = set()
    for path in [*COMP.glob("*.py"), *(COMP / "www").glob("*.js")]:
        used |= set(re.findall(r"mdi:([a-z0-9-]+)", path.read_text(encoding="utf-8")))
    used.discard("wrench")  # placeholder text in the icon input, not rendered as an icon
    missing = sorted(used - names)
    assert not missing, missing
