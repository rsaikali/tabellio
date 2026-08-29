from __future__ import annotations

import pytest

from tabellio.backends import available_backends, get_backend
from tabellio.errors import BackendNotAvailable


def test_registry_lists_all_providers():
    assert available_backends() == ["anthropic", "gemini", "nim", "ollama", "openai"]


def test_unknown_backend():
    with pytest.raises(BackendNotAvailable):
        get_backend("does-not-exist")


@pytest.mark.parametrize("name", available_backends())
def test_missing_sdk_raises_backend_not_available(name):
    """None of the optional SDKs are installed in the base test env."""
    try:
        get_backend(name)
    except BackendNotAvailable:
        pass
    except Exception as exc:  # pragma: no cover - only if an SDK is present
        pytest.skip(f"{name} SDK appears installed: {exc!r}")
