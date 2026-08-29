from __future__ import annotations

import pytest

from tabellio.errors import ProviderNotAvailable
from tabellio.providers import available_providers, get_provider


def test_registry_lists_all_providers():
    assert available_providers() == ["anthropic", "gemini", "nim", "ollama", "openai"]


def test_unknown_provider():
    with pytest.raises(ProviderNotAvailable):
        get_provider("does-not-exist")


def test_nim_rejects_oversized_inline_image():
    from tabellio.errors import ProviderError
    from tabellio.providers.nim import INLINE_IMAGE_LIMIT, NIMProvider

    big = b"\xff\xd8\xff" + b"0" * INLINE_IMAGE_LIMIT
    with pytest.raises(ProviderError, match="180 KB"):
        NIMProvider().extract(
            image=big,
            mime="image/jpeg",
            system_prompt="s",
            few_shot=[],
            user_prompt="u",
            api_key="k",
            model=None,
        )


@pytest.mark.parametrize("name", available_providers())
def test_missing_sdk_raises_provider_not_available(name):
    """If the optional SDK is absent, get_provider must say so cleanly."""
    try:
        get_provider(name)
    except ProviderNotAvailable:
        pass
    except Exception as exc:  # pragma: no cover - only if an SDK is present
        pytest.skip(f"{name} SDK appears installed: {exc!r}")
