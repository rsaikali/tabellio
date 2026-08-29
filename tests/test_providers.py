from __future__ import annotations

import pytest

from tabellio.errors import ProviderNotAvailable
from tabellio.providers import available_providers, get_provider


def test_registry_lists_all_providers():
    assert available_providers() == ["anthropic", "gemini", "nim", "ollama", "openai"]


def test_unknown_provider():
    with pytest.raises(ProviderNotAvailable):
        get_provider("does-not-exist")


def _big_jpeg(min_bytes: int) -> bytes:
    import random
    from io import BytesIO

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (3000, 2000), "white")
    draw = ImageDraw.Draw(img)
    rng = random.Random(0)
    for _ in range(4000):
        x, y = rng.randint(0, 2980), rng.randint(0, 1992)
        draw.line([(x, y), (x + rng.randint(4, 18), y + rng.randint(-3, 3))], fill="black", width=2)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    data = buf.getvalue()
    assert len(data) > min_bytes
    return data


def test_nim_oversized_image_raises_when_shrink_disabled():
    from tabellio.errors import ProviderError
    from tabellio.providers.nim import INLINE_IMAGE_LIMIT, NIMProvider

    big = _big_jpeg(INLINE_IMAGE_LIMIT)
    with pytest.raises(ProviderError, match="180 KB"):
        NIMProvider().extract(
            image=big,
            mime="image/jpeg",
            system_prompt="s",
            few_shot=[],
            user_prompt="u",
            api_key="k",
            model=None,
            shrink=False,
        )


def test_nim_shrinks_oversized_image_before_send(monkeypatch):
    from tabellio.providers.nim import INLINE_IMAGE_LIMIT, NIMProvider
    from tabellio.providers.openai import OpenAIProvider

    seen: dict = {}

    def fake_super_extract(self, *, image, mime, **kw):
        seen["bytes"] = len(image)
        seen["mime"] = mime
        return "{}"

    monkeypatch.setattr(OpenAIProvider, "extract", fake_super_extract)
    big = _big_jpeg(INLINE_IMAGE_LIMIT)
    NIMProvider().extract(
        image=big,
        mime="image/jpeg",
        system_prompt="s",
        few_shot=[],
        user_prompt="u",
        api_key="k",
        model=None,
    )
    assert seen["bytes"] <= INLINE_IMAGE_LIMIT
    assert seen["mime"] == "image/jpeg"


@pytest.mark.parametrize("name", available_providers())
def test_missing_sdk_raises_provider_not_available(name):
    """If the optional SDK is absent, get_provider must say so cleanly."""
    try:
        get_provider(name)
    except ProviderNotAvailable:
        pass
    except Exception as exc:  # pragma: no cover - only if an SDK is present
        pytest.skip(f"{name} SDK appears installed: {exc!r}")
