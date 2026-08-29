"""``tabellio.parse`` -- the one public entry point."""

from __future__ import annotations

import json
import os

from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from tabellio import prompt as _prompt
from tabellio.errors import SchemaMismatch
from tabellio.image import ImageInput, load_image
from tabellio.providers import DEFAULT_PROVIDER, get_provider
from tabellio.schema import Act
from tabellio.validate import validate as _validate

#: The only three environment variables tabellio itself reads. Each is a
#: fallback for the matching ``parse()`` argument; an explicit argument wins.
ENV_PROVIDER = "TABELLIO_PROVIDER"
ENV_KEY = "TABELLIO_KEY"
ENV_MODEL = "TABELLIO_MODEL"


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _pick(explicit: str | None, env_var: str, default: str | None = None) -> str | None:
    if explicit:
        return explicit
    return os.environ.get(env_var) or default


def parse(
    image: ImageInput,
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    act_type_hint: str | None = None,
    validate: bool = True,
    **provider_options: object,
) -> Act:
    """Extract a structured :class:`Act` from an image of a single record.

    Parameters
    ----------
    image:
        Path, bytes or file-like object. jpeg / png / tiff / webp.
    provider:
        ``"gemini" | "openai" | "nim" | "anthropic" | "ollama"``. Falls back to
        ``$TABELLIO_PROVIDER``, then ``"gemini"``.
    api_key:
        The caller's own provider key (BYOK). Never stored, never logged. Falls
        back to ``$TABELLIO_KEY``. Not required for ``ollama``.
    model:
        Override the provider's default model id. Falls back to
        ``$TABELLIO_MODEL``.
    act_type_hint:
        Optional caller guess (``"birth"``, ``"marriage"``...). The model still
        verifies it against the image.
    validate:
        Run :mod:`tabellio.validate` consistency rules and fill ``act.warnings``.
    """
    provider = _pick(provider, ENV_PROVIDER, DEFAULT_PROVIDER)
    api_key = _pick(api_key, ENV_KEY)
    model = _pick(model, ENV_MODEL)

    data, mime = load_image(image)
    impl = get_provider(provider)
    logger.debug(
        "tabellio.parse provider={} model={} bytes={} mime={} prompt_v={}",
        provider,
        model or "<default>",
        len(data),
        mime,
        _prompt.PROMPT_VERSION,
    )

    raw = impl.extract(
        image=data,
        mime=mime,
        system_prompt=_prompt.SYSTEM_PROMPT,
        few_shot=_prompt.few_shot(),
        user_prompt=_prompt.user_prompt(act_type_hint),
        api_key=api_key,
        model=model,
        **provider_options,
    )

    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise SchemaMismatch(f"provider {provider!r} did not return JSON: {exc}", raw=raw) from exc

    try:
        act = Act.model_validate(payload)
    except PydanticValidationError as exc:
        raise SchemaMismatch(
            f"provider {provider!r} output failed schema validation:\n{exc}", raw=payload
        ) from exc

    act.prompt_version = _prompt.PROMPT_VERSION
    act.provider = provider
    return _validate(act) if validate else act
