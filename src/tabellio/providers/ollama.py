"""Ollama provider for a local VLM (``pip install 'tabellio[ollama]'``).

Optional and local -- no API key needed. Reliability caveat from CLAUDE.md
applies: local general-purpose VLMs hallucinate on old cursive.
"""

from __future__ import annotations

from ollama import Client

from tabellio.errors import ProviderError

DEFAULT_MODEL = "llama3.2-vision"
DEFAULT_HOST = "http://localhost:11434"
DEFAULT_TIMEOUT = 120.0


class OllamaProvider:
    name = "ollama"

    def extract(
        self,
        *,
        image: bytes,
        mime: str,
        system_prompt: str,
        few_shot: list[dict[str, str]],
        user_prompt: str,
        api_key: str | None = None,
        model: str | None,
        host: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        **options: object,
    ) -> str:
        client = Client(host=host or DEFAULT_HOST, timeout=timeout)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in few_shot]
        messages.append({"role": "user", "content": user_prompt, "images": [image]})
        try:
            resp = client.chat(
                model=model or DEFAULT_MODEL,
                messages=messages,
                format="json",
                options={"temperature": 0},
            )
        except Exception as exc:
            raise ProviderError(f"ollama call failed: {exc}") from exc
        text = (resp.get("message") or {}).get("content", "").strip()
        if not text:
            raise ProviderError("ollama returned an empty response")
        return text
