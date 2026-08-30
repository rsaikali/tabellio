"""Provider interface and registry.

A provider turns ``(image, prompt) -> raw JSON string`` for one VLM vendor. It
must not store, cache or log the image or the API key.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tabellio.errors import ProviderNotAvailable

DEFAULT_PROVIDER = "gemini"


@runtime_checkable
class Provider(Protocol):
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
    "gemini": "tabellio.providers.gemini:GeminiProvider",
    "openai": "tabellio.providers.openai:OpenAIProvider",
    "nim": "tabellio.providers.nim:NIMProvider",
    "anthropic": "tabellio.providers.anthropic:AnthropicProvider",
    "mistral": "tabellio.providers.mistral:MistralProvider",
    "ollama": "tabellio.providers.ollama:OllamaProvider",
}


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


def get_provider(name: str) -> Provider:
    try:
        target = _REGISTRY[name]
    except KeyError:
        raise ProviderNotAvailable(
            f"unknown provider {name!r}; choose one of {available_providers()}"
        ) from None
    module_path, cls_name = target.split(":")
    import importlib

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:  # optional SDK missing
        raise ProviderNotAvailable(
            f"provider {name!r} needs an extra: pip install 'tabellio[{name}]' ({exc})"
        ) from exc
    return getattr(module, cls_name)()
