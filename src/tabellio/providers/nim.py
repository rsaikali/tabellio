"""NVIDIA NIM provider -- OpenAI-compatible endpoint (``pip install 'tabellio[nim]'``).

Constraints of the hosted endpoint (integrate.api.nvidia.com):
- inline base64 images must be <= ~180 KB; larger images require the NVCF asset
  upload API, which this provider does not implement yet.
- the free tier queues requests; cold starts of ~1-3 min are normal.
"""

from __future__ import annotations

from tabellio.errors import ProviderError
from tabellio.providers.openai import OpenAIProvider

DEFAULT_MODEL = "meta/llama-3.2-90b-vision-instruct"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

#: NVCF rejects inline images larger than this; measured on the raw bytes.
INLINE_IMAGE_LIMIT = 180_000


class NIMProvider(OpenAIProvider):
    name = "nim"

    def extract(
        self,
        *,
        image: bytes,
        model: str | None = None,
        base_url: str | None = None,
        **kw: object,
    ) -> str:
        if len(image) > INLINE_IMAGE_LIMIT:
            raise ProviderError(
                f"NIM rejects inline images larger than ~{INLINE_IMAGE_LIMIT // 1000} KB; "
                f"this one is {len(image) // 1000} KB. Use a smaller image, or another "
                "provider (gemini reads acts well). NVCF asset upload for large images "
                "is not implemented yet."
            )
        return super().extract(
            image=image,
            model=model or DEFAULT_MODEL,
            base_url=base_url or DEFAULT_BASE_URL,
            **kw,
        )
