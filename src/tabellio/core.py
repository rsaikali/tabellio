"""``tabellio.parse`` -- the one public entry point."""

from __future__ import annotations

import json

from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from tabellio import prompt as _prompt
from tabellio.backends import get_backend
from tabellio.errors import SchemaMismatch
from tabellio.image import ImageInput, load_image
from tabellio.schema import Act
from tabellio.validate import validate as _validate


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def parse(
    image: ImageInput,
    *,
    backend: str = "gemini",
    api_key: str | None = None,
    act_type_hint: str | None = None,
    model: str | None = None,
    validate: bool = True,
    **backend_options: object,
) -> Act:
    """Extract a structured :class:`Act` from an image of a single record.

    Parameters
    ----------
    image:
        Path, bytes or file-like object. jpeg / png / tiff / webp.
    backend:
        ``"gemini" | "openai" | "nim" | "anthropic" | "ollama"``.
    api_key:
        The caller's own provider key (BYOK). Never stored, never logged.
        Not required for ``ollama``.
    act_type_hint:
        Optional caller guess (``"birth"``, ``"marriage"``...). The model still
        verifies it against the image.
    model:
        Override the backend's default model id.
    validate:
        Run :mod:`tabellio.validate` consistency rules and fill ``act.warnings``.
    """
    data, mime = load_image(image)
    impl = get_backend(backend)
    logger.debug(
        "tabellio.parse backend={} model={} bytes={} mime={} prompt_v={}",
        backend,
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
        **backend_options,
    )

    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise SchemaMismatch(f"backend {backend!r} did not return JSON: {exc}", raw=raw) from exc

    try:
        act = Act.model_validate(payload)
    except PydanticValidationError as exc:
        raise SchemaMismatch(
            f"backend {backend!r} output failed schema validation:\n{exc}", raw=payload
        ) from exc

    act.prompt_version = _prompt.PROMPT_VERSION
    act.backend = backend
    return _validate(act) if validate else act
