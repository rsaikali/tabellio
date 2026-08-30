"""Mistral provider (``pip install 'tabellio[mistral]'``).

Paid (Mistral has no free tier as of writing). The default
``mistral-small-latest`` is fast and cheap; ``mistral-medium-latest`` reads
harder hands better. The old ``pixtral-*`` models are deprecated -- their vision
is folded into Small / Medium now. Heavy old cursive is still better served by
``gemini``.
"""

from __future__ import annotations

from mistralai.client import Mistral  # mistralai 2.x layout

from tabellio.errors import ProviderError
from tabellio.image import to_data_url

DEFAULT_MODEL = "mistral-small-latest"
DEFAULT_TIMEOUT = 120.0


class MistralProvider:
    name = "mistral"

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
        timeout: float = DEFAULT_TIMEOUT,
        **options: object,
    ) -> str:
        if not api_key:
            raise ProviderError("mistral provider requires an API key (BYOK)")
        client = Mistral(api_key=api_key, timeout_ms=int(timeout * 1000))
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in few_shot]
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": to_data_url(image, mime)},
                ],
            }
        )
        try:
            resp = client.chat.complete(
                model=model or DEFAULT_MODEL,
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise ProviderError(f"mistral call failed: {exc}") from exc

        content = resp.choices[0].message.content if resp.choices else None
        if isinstance(content, list):  # newer SDK returns content chunks
            content = "".join(getattr(c, "text", "") for c in content)
        text = (content or "").strip()
        if not text:
            raise ProviderError("mistral returned an empty response")
        return text
