from __future__ import annotations

import base64

import pytest

# 1x1 transparent PNG, public-domain trivial asset (not a scanned record).
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)

FICTIONAL_ACT = {
    "type": "death",
    "date": {
        "raw": "le trois janvier mil huit cent douze",
        "iso": "1812-01-03",
        "confidence": 0.85,
    },
    "place": {"value": "Bourg-Fictif", "raw": "Bourg Fictif", "confidence": 0.6},
    "persons": [
        {
            "role": "subject",
            "given": {"value": "Anonyme", "raw": "Anonyme", "confidence": 0.9},
            "surname": {"value": "Untel", "raw": "Untel", "confidence": 0.3},
        }
    ],
    "other": [],
    "source_hint": "civil",
}


FICTIONAL_SUMMARY = {
    "type": "death",
    "date": "1812-01-03",
    "location": "Bourg-Fictif",
    "persons": [
        {"role": "subject", "given": "Anonyme", "surname": "Untel"},
    ],
}

FICTIONAL_TRANSCRIPTION = {
    "text": "L'an 1812, le 3 janvier, est decede Anonyme Untel a Bourg-Fictif [?].",
    "language": "fr",
}


@pytest.fixture(autouse=True)
def _clear_tabellio_env(monkeypatch):
    """Isolate every test from the developer's own TABELLIO_* environment."""
    for var in ("TABELLIO_PROVIDER", "TABELLIO_KEY", "TABELLIO_MODEL"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def png_bytes() -> bytes:
    return PNG_1X1


@pytest.fixture
def fictional_act() -> dict:
    return dict(FICTIONAL_ACT)


@pytest.fixture
def fictional_summary() -> dict:
    return dict(FICTIONAL_SUMMARY)


@pytest.fixture
def fictional_transcription() -> dict:
    return dict(FICTIONAL_TRANSCRIPTION)


class FakeProvider:
    """Deterministic provider for tests -- returns whatever text it is given."""

    name = "fake"

    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[dict] = []

    def extract(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return self._response


@pytest.fixture
def fake_provider(monkeypatch):
    def _install(response: str) -> FakeProvider:
        impl = FakeProvider(response)
        monkeypatch.setattr("tabellio.core.get_provider", lambda name: impl)
        return impl

    return _install
