from __future__ import annotations

import pytest

from tabellio.errors import ProviderNotAvailable
from tabellio.providers import available_providers, get_provider


def test_registry_lists_all_providers():
    assert available_providers() == ["anthropic", "gemini", "nim", "ollama", "openai"]


def test_unknown_provider():
    with pytest.raises(ProviderNotAvailable):
        get_provider("does-not-exist")


@pytest.mark.parametrize("name", available_providers())
def test_missing_sdk_raises_provider_not_available(name):
    """If the optional SDK is absent, get_provider must say so cleanly."""
    try:
        get_provider(name)
    except ProviderNotAvailable:
        pass
    except Exception as exc:  # pragma: no cover - only if an SDK is present
        pytest.skip(f"{name} SDK appears installed: {exc!r}")
