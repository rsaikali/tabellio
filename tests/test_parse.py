from __future__ import annotations

import json

import pytest

from tabellio import parse
from tabellio.errors import SchemaMismatch


def test_parse_happy_path(png_bytes, fictional_act, fake_backend):
    be = fake_backend(json.dumps(fictional_act))
    act = parse(png_bytes, backend="fake", api_key="k")
    assert act.type == "death"
    assert act.backend == "fake"
    assert act.prompt_version == "1"
    # BYOK key is forwarded, not swallowed
    assert be.calls[0]["api_key"] == "k"


def test_parse_reads_key_from_env(png_bytes, fictional_act, fake_backend, monkeypatch):
    monkeypatch.delenv("TABELLIO_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "from-env")
    be = fake_backend(json.dumps(fictional_act))
    parse(png_bytes, backend="gemini")
    assert be.calls[0]["api_key"] == "from-env"


def test_parse_explicit_key_beats_env(png_bytes, fictional_act, fake_backend, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "from-env")
    be = fake_backend(json.dumps(fictional_act))
    parse(png_bytes, backend="gemini", api_key="explicit")
    assert be.calls[0]["api_key"] == "explicit"


def test_parse_tabellio_api_key_wins_over_provider_var(
    png_bytes, fictional_act, fake_backend, monkeypatch
):
    monkeypatch.setenv("TABELLIO_API_KEY", "generic")
    monkeypatch.setenv("GEMINI_API_KEY", "provider")
    be = fake_backend(json.dumps(fictional_act))
    parse(png_bytes, backend="gemini")
    assert be.calls[0]["api_key"] == "generic"


def test_parse_strips_markdown_fences(png_bytes, fictional_act, fake_backend):
    fake_backend("```json\n" + json.dumps(fictional_act) + "\n```")
    act = parse(png_bytes, backend="fake", api_key="k")
    assert act.type == "death"


def test_parse_non_json(png_bytes, fake_backend):
    fake_backend("I could not read this act, sorry.")
    with pytest.raises(SchemaMismatch):
        parse(png_bytes, backend="fake", api_key="k")


def test_parse_schema_mismatch(png_bytes, fake_backend):
    fake_backend(json.dumps({"type": "not-a-real-type", "date": {}}))
    with pytest.raises(SchemaMismatch):
        parse(png_bytes, backend="fake", api_key="k")


def test_parse_runs_validation(png_bytes, fake_backend):
    fake_backend(
        json.dumps(
            {
                "type": "marriage",
                "date": {"raw": "x", "iso": "1830-01-01", "confidence": 0.9},
                "persons": [{"role": "groom"}],
            }
        )
    )
    act = parse(png_bytes, backend="fake", api_key="k")
    assert any("bride" in w for w in act.warnings)


def test_parse_validation_can_be_disabled(png_bytes, fake_backend):
    fake_backend(
        json.dumps(
            {
                "type": "marriage",
                "date": {"raw": "x", "iso": "1830-01-01", "confidence": 0.9},
                "persons": [{"role": "groom"}],
            }
        )
    )
    act = parse(png_bytes, backend="fake", api_key="k", validate=False)
    assert act.warnings == []
