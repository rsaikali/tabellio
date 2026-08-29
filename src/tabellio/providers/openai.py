"""OpenAI provider (``pip install 'tabellio[openai]'``)."""

from __future__ import annotations

from openai import OpenAI

from tabellio.errors import ProviderError
from tabellio.image import to_data_url

DEFAULT_MODEL = "gpt-4o"
DEFAULT_BASE_URL: str | None = None


class OpenAIProvider:
    name = "openai"

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
        base_url: str | None = None,
        **options: object,
    ) -> str:
        if not api_key:
            raise ProviderError(f"{self.name} provider requires an API key (BYOK)")
        client = OpenAI(api_key=api_key, base_url=base_url or DEFAULT_BASE_URL)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in few_shot]
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": to_data_url(image, mime)}},
                ],
            }
        )
        try:
            resp = client.chat.completions.create(
                model=model or DEFAULT_MODEL,
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise ProviderError(f"{self.name} call failed: {exc}") from exc
        text = resp.choices[0].message.content if resp.choices else None
        if not text:
            raise ProviderError(f"{self.name} returned an empty response")
        return text
