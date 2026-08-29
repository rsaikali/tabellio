"""Common backend interface and registry.

A backend turns ``(image, prompt) -> raw JSON string`` for one provider. It must
not store, cache or log the image or the API key.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tabellio.errors import BackendNotAvailable


@runtime_checkable
class Backend(Protocol):
    name: str

    def extract(
        self,
        *,
        image: bytes,
        mime: str,
        system_prompt: str,
        few_shot: list[dict[str, str]],
        user_prompt: str,
        api_key: str | None,
        model: str | None,
        **options: object,
    ) -> str:
        """Return the provider's raw response text (expected to be JSON)."""
        ...


_REGISTRY: dict[str, str] = {
    "gemini": "tabellio.backends.gemini:GeminiBackend",
    "openai": "tabellio.backends.openai:OpenAIBackend",
    "nim": "tabellio.backends.nim:NIMBackend",
    "anthropic": "tabellio.backends.anthropic:AnthropicBackend",
    "ollama": "tabellio.backends.ollama:OllamaBackend",
}


def available_backends() -> list[str]:
    return sorted(_REGISTRY)


def get_backend(name: str) -> Backend:
    try:
        target = _REGISTRY[name]
    except KeyError:
        raise BackendNotAvailable(
            f"unknown backend {name!r}; choose one of {available_backends()}"
        ) from None
    module_path, cls_name = target.split(":")
    import importlib

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:  # optional SDK missing
        raise BackendNotAvailable(
            f"backend {name!r} needs an extra: pip install 'tabellio[{name}]' ({exc})"
        ) from exc
    return getattr(module, cls_name)()
