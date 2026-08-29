"""NVIDIA NIM backend -- OpenAI-compatible endpoint (``pip install 'tabellio[nim]'``)."""

from __future__ import annotations

from tabellio.backends.openai import OpenAIBackend

DEFAULT_MODEL = "meta/llama-3.2-90b-vision-instruct"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NIMBackend(OpenAIBackend):
    name = "nim"

    def extract(
        self, *, model: str | None = None, base_url: str | None = None, **kw: object
    ) -> str:
        return super().extract(
            model=model or DEFAULT_MODEL,
            base_url=base_url or DEFAULT_BASE_URL,
            **kw,
        )
