"""Google Gemini provider (``pip install 'tabellio[gemini]'``)."""

from __future__ import annotations

from google import genai
from google.genai import types

from tabellio.errors import ProviderError

DEFAULT_MODEL = "gemini-3.6-flash"


class GeminiProvider:
    name = "gemini"

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
        if not api_key:
            raise ProviderError("gemini provider requires an API key (BYOK)")
        client = genai.Client(api_key=api_key)
        contents = [types.Part.from_text(text=m["content"]) for m in few_shot]
        contents += [
            types.Part.from_text(text=user_prompt),
            types.Part.from_bytes(data=image, mime_type=mime),
        ]
        try:
            resp = client.models.generate_content(
                model=model or DEFAULT_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0,
                    # No tools are passed; disabling AFC silences the SDK warning.
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except Exception as exc:
            raise ProviderError(f"gemini call failed: {exc}") from exc
        text = resp.text
        if not text:
            raise ProviderError("gemini returned an empty response")
        return text
