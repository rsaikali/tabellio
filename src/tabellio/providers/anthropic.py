"""Anthropic provider (``pip install 'tabellio[anthropic]'``)."""

from __future__ import annotations

import base64

import anthropic

from tabellio.errors import ProviderError

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicProvider:
    name = "anthropic"

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
        max_tokens: int = 4096,
        **options: object,
    ) -> str:
        if not api_key:
            raise ProviderError("anthropic provider requires an API key (BYOK)")
        client = anthropic.Anthropic(api_key=api_key)
        messages: list[dict] = [{"role": m["role"], "content": m["content"]} for m in few_shot]
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": base64.b64encode(image).decode("ascii"),
                        },
                    },
                ],
            }
        )
        try:
            resp = client.messages.create(
                model=model or DEFAULT_MODEL,
                system=system_prompt,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0,
            )
        except Exception as exc:
            raise ProviderError(f"anthropic call failed: {exc}") from exc
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        text = "".join(parts).strip()
        if not text:
            raise ProviderError("anthropic returned an empty response")
        return text
