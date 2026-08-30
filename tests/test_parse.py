from __future__ import annotations

import json

import pytest

from tabellio import ActSummary, parse
from tabellio import prompt as _prompt
from tabellio.errors import SchemaMismatch


def test_parse_happy_path(png_bytes, fictional_act, fake_provider):
    impl = fake_provider(json.dumps(fictional_act))
    act = parse(png_bytes, provider="fake", api_key="k")
    assert act.type == "death"
    assert act.provider == "fake"
    # BYOK key is forwarded, not swallowed
    assert impl.calls[0]["api_key"] == "k"


def test_parse_defaults_to_gemini(png_bytes, fictional_act, fake_provider):
    fake_provider(json.dumps(fictional_act))
    act = parse(png_bytes, api_key="k")
    assert act.provider == "gemini"


def test_parse_provider_from_env(png_bytes, fictional_act, fake_provider, monkeypatch):
    monkeypatch.setenv("TABELLIO_PROVIDER", "nim")
    fake_provider(json.dumps(fictional_act))
    act = parse(png_bytes, api_key="k")
    assert act.provider == "nim"


def test_parse_key_from_env(png_bytes, fictional_act, fake_provider, monkeypatch):
    monkeypatch.setenv("TABELLIO_KEY", "from-env")
    impl = fake_provider(json.dumps(fictional_act))
    parse(png_bytes, provider="fake")
    assert impl.calls[0]["api_key"] == "from-env"


def test_parse_model_from_env(png_bytes, fictional_act, fake_provider, monkeypatch):
    monkeypatch.setenv("TABELLIO_MODEL", "qwen/qwen2.5-vl-72b-instruct")
    impl = fake_provider(json.dumps(fictional_act))
    parse(png_bytes, provider="fake", api_key="k")
    assert impl.calls[0]["model"] == "qwen/qwen2.5-vl-72b-instruct"


def test_parse_explicit_args_beat_env(png_bytes, fictional_act, fake_provider, monkeypatch):
    monkeypatch.setenv("TABELLIO_PROVIDER", "nim")
    monkeypatch.setenv("TABELLIO_KEY", "env-key")
    monkeypatch.setenv("TABELLIO_MODEL", "env-model")
    impl = fake_provider(json.dumps(fictional_act))
    act = parse(png_bytes, provider="fake", api_key="arg-key", model="arg-model")
    assert act.provider == "fake"
    assert impl.calls[0]["api_key"] == "arg-key"
    assert impl.calls[0]["model"] == "arg-model"


def test_parse_language_hint_reaches_prompt(png_bytes, fictional_act, fake_provider):
    impl = fake_provider(json.dumps(fictional_act))
    parse(png_bytes, provider="fake", api_key="k", act_language_hint="la")
    assert "written in la" in impl.calls[0]["user_prompt"]


def test_parse_no_language_hint_no_language_line(png_bytes, fictional_act, fake_provider):
    impl = fake_provider(json.dumps(fictional_act))
    parse(png_bytes, provider="fake", api_key="k")
    assert "believes the act is written" not in impl.calls[0]["user_prompt"]


def test_parse_simple_mode_returns_summary(png_bytes, fictional_summary, fake_provider):
    impl = fake_provider(json.dumps(fictional_summary))
    act = parse(png_bytes, provider="fake", api_key="k", output_mode="simple")
    assert isinstance(act, ActSummary)
    assert act.type == "death"
    assert act.date == "1812-01-03"
    assert act.location == "Bourg-Fictif"
    assert act.persons[0].given == "Anonyme"
    assert act.transcription.startswith("L'an 1812")
    # simple mode uses its own shorter prompt, not the full one
    assert impl.calls[0]["system_prompt"] == _prompt.system_prompt("simple")
    assert impl.calls[0]["system_prompt"] != _prompt.system_prompt("full")


def test_parse_simple_mode_has_no_meta_or_warnings(png_bytes, fictional_summary, fake_provider):
    fake_provider(json.dumps(fictional_summary))
    act = parse(png_bytes, provider="fake", api_key="k", output_mode="simple")
    assert not hasattr(act, "warnings")
    assert not hasattr(act, "provider")
    assert not hasattr(act, "confidence")


def test_parse_simple_mode_rejects_full_payload(png_bytes, fictional_act, fake_provider):
    fake_provider(json.dumps(fictional_act))
    with pytest.raises(SchemaMismatch):
        parse(png_bytes, provider="fake", api_key="k", output_mode="simple")


def test_parse_full_mode_is_default(png_bytes, fictional_act, fake_provider):
    fake_provider(json.dumps(fictional_act))
    act = parse(png_bytes, provider="fake", api_key="k")
    assert not isinstance(act, ActSummary)
    assert act.provider == "fake"


def test_parse_bad_output_mode(png_bytes, fake_provider):
    fake_provider("{}")
    with pytest.raises(ValueError, match="output_mode"):
        parse(png_bytes, provider="fake", api_key="k", output_mode="tiny")


def test_parse_strips_markdown_fences(png_bytes, fictional_act, fake_provider):
    fake_provider("```json\n" + json.dumps(fictional_act) + "\n```")
    act = parse(png_bytes, provider="fake", api_key="k")
    assert act.type == "death"


def test_parse_non_json(png_bytes, fake_provider):
    fake_provider("I could not read this act, sorry.")
    with pytest.raises(SchemaMismatch):
        parse(png_bytes, provider="fake", api_key="k")


def test_parse_schema_mismatch(png_bytes, fake_provider):
    fake_provider(json.dumps({"type": "not-a-real-type", "date": {}}))
    with pytest.raises(SchemaMismatch):
        parse(png_bytes, provider="fake", api_key="k")


def test_parse_runs_validation(png_bytes, fake_provider):
    fake_provider(
        json.dumps(
            {
                "type": "marriage",
                "date": {"raw": "x", "iso": "1830-01-01", "confidence": 0.9},
                "persons": [{"role": "groom"}],
            }
        )
    )
    act = parse(png_bytes, provider="fake", api_key="k")
    assert any("bride" in w for w in act.warnings)


def test_parse_validation_can_be_disabled(png_bytes, fake_provider):
    fake_provider(
        json.dumps(
            {
                "type": "marriage",
                "date": {"raw": "x", "iso": "1830-01-01", "confidence": 0.9},
                "persons": [{"role": "groom"}],
            }
        )
    )
    act = parse(png_bytes, provider="fake", api_key="k", validate=False)
    assert act.warnings == []
