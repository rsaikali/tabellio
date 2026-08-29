"""NVIDIA NIM provider -- OpenAI-compatible endpoint (``pip install 'tabellio[nim]'``).

Constraints of the hosted endpoint (integrate.api.nvidia.com):
- inline base64 images must be <= ~180 KB; larger ones are re-encoded smaller in
  memory before sending (the source file is never touched). NVCF asset upload
  for large images is not implemented.
- the free tier queues requests; cold starts of ~1-3 min are normal.
"""

from __future__ import annotations

from loguru import logger

from tabellio.errors import ProviderError
from tabellio.image import fit_within
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
        mime: str,
        model: str | None = None,
        base_url: str | None = None,
        shrink: bool = True,
        **kw: object,
    ) -> str:
        if len(image) > INLINE_IMAGE_LIMIT:
            if not shrink:
                raise ProviderError(
                    f"NIM rejects inline images larger than ~{INLINE_IMAGE_LIMIT // 1000} KB; "
                    f"this one is {len(image) // 1000} KB. Pass shrink=True, use a smaller "
                    "image, or another provider."
                )
            original = len(image)
            image, mime = fit_within(image, INLINE_IMAGE_LIMIT)
            logger.warning(
                "NIM: image re-encoded in memory {} KB -> {} KB to fit the ~{} KB inline "
                "limit; extraction quality may drop. Source file untouched.",
                original // 1000,
                len(image) // 1000,
                INLINE_IMAGE_LIMIT // 1000,
            )
        return super().extract(
            image=image,
            mime=mime,
            model=model or DEFAULT_MODEL,
            base_url=base_url or DEFAULT_BASE_URL,
            **kw,
        )
