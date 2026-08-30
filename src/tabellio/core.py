"""``tabellio.parse`` -- the one public entry point."""

from __future__ import annotations

import json
import os
from typing import Literal

from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from tabellio import prompt as _prompt
from tabellio.errors import SchemaMismatch
from tabellio.image import ImageInput, load_image
from tabellio.providers import DEFAULT_PROVIDER, get_provider
from tabellio.schema import Act, ActSummary, Transcription
from tabellio.validate import validate as _validate

#: The only three environment variables tabellio itself reads. Each is a
#: fallback for the matching ``parse()`` argument; an explicit argument wins.
ENV_PROVIDER = "TABELLIO_PROVIDER"
ENV_KEY = "TABELLIO_KEY"
ENV_MODEL = "TABELLIO_MODEL"

OutputMode = Literal["full", "simple", "transcription"]
_TARGET: dict[str, type] = {"full": Act, "simple": ActSummary, "transcription": Transcription}


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
    act_language_hint: str | None = None,
    output_mode: OutputMode = "full",
    validate: bool = True,
    **provider_options: object,
) -> Act | ActSummary | Transcription:
    """Extract a structured act from an image of a single record.

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
    act_language_hint:
        Optional caller guess at the act's language (``"fr"``, ``"la"``,
        ``"de"``...). The model still verifies it and records the detected
        language on ``act.language``. Text is transcribed in the source
        language, never translated.
    output_mode:
        - ``"full"`` (default): a rich :class:`~tabellio.schema.Act` -- raw
          spelling, per-field ``confidence``, date ``qualifier``,
          ``transcription``, validation ``warnings``.
        - ``"simple"``: a bare :class:`~tabellio.schema.ActSummary` -- ``type``,
          ``date``, ``location``, ``persons`` (role / given / surname), nothing
          else. Shorter prompt, fewer tokens.
        - ``"transcription"``: just :class:`~tabellio.schema.Transcription`
          (``text`` + detected ``language``) -- the verbatim text, no structure.
    validate:
        Run :mod:`tabellio.validate` consistency rules and fill ``act.warnings``.
        ``"full"`` only.
    **provider_options:
        Passed straight to the provider, e.g. ``timeout`` (seconds, default 120),
        ``base_url``, ``host``, ``max_tokens``.
    """
    if output_mode not in _TARGET:
        raise ValueError(f"output_mode must be one of {sorted(_TARGET)}, got {output_mode!r}")

    provider = _pick(provider, ENV_PROVIDER, DEFAULT_PROVIDER)
    api_key = _pick(api_key, ENV_KEY)
    model = _pick(model, ENV_MODEL)

    data, mime = load_image(image)
    impl = get_provider(provider)
    logger.debug(
        "tabellio.parse provider={} model={} mode={} bytes={} mime={}",
        provider,
        model or "<default>",
        output_mode,
        len(data),
        mime,
    )

    raw = impl.extract(
        image=data,
        mime=mime,
        system_prompt=_prompt.system_prompt(output_mode),
        few_shot=_prompt.few_shot(output_mode),
        user_prompt=_prompt.user_prompt(act_type_hint, output_mode, act_language_hint),
        api_key=api_key,
        model=model,
        **provider_options,
    )

    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise SchemaMismatch(f"provider {provider!r} did not return JSON: {exc}", raw=raw) from exc

    target = _TARGET[output_mode]
    try:
        result = target.model_validate(payload)
    except PydanticValidationError as exc:
        raise SchemaMismatch(
            f"provider {provider!r} output failed {output_mode} schema validation:\n{exc}",
            raw=payload,
        ) from exc

    if not isinstance(result, Act):
        return result  # ActSummary / Transcription -- no meta, no validation

    result.provider = provider
    return _validate(result) if validate else result
