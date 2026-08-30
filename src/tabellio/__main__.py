"""``python -m tabellio <image>`` -- quick manual check against one record.

Configuration comes from the environment (see ``tabellio.parse``):
``TABELLIO_PROVIDER``, ``TABELLIO_KEY``, ``TABELLIO_MODEL``. The key is never a
CLI argument, so it cannot land in shell history.
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from tabellio import parse, to_gedcom
from tabellio.errors import TabellioError
from tabellio.providers import available_providers
from tabellio.schema import Act, Transcription


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tabellio")
    ap.add_argument("image", help="path to an image of a single record")
    ap.add_argument(
        "--provider",
        default=None,
        choices=available_providers(),
        help="override $TABELLIO_PROVIDER (default: gemini)",
    )
    ap.add_argument(
        "--model",
        default=None,
        help="override $TABELLIO_MODEL / the provider default",
    )
    ap.add_argument(
        "--hint",
        default=None,
        choices=["birth", "baptism", "marriage", "death", "burial"],
        help="act type hint (still verified against the image)",
    )
    ap.add_argument(
        "--lang",
        default=None,
        metavar="ISO",
        help="act language hint, ISO 639-1 e.g. fr, la, de (still verified)",
    )
    ap.add_argument(
        "--context",
        default=None,
        metavar="TEXT",
        help="free text you already know about the act (names, a date, a place); "
        "used only to disambiguate, never to override a clear reading",
    )
    ap.add_argument(
        "--output",
        default="full",
        choices=["full", "simple", "transcription"],
        help="full: rich Act; simple: bare summary; transcription: verbatim text only",
    )
    ap.add_argument(
        "--format",
        default="json",
        choices=["json", "gedcom"],
        help="json (default) or a GEDCOM 7 document (implies --output full)",
    )
    ap.add_argument("--no-validate", action="store_true", help="skip consistency rules (full only)")
    ap.add_argument("-v", "--verbose", action="store_true", help="show debug logs")
    args = ap.parse_args(argv)

    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.verbose else "WARNING")

    output_mode = "full" if args.format == "gedcom" else args.output
    try:
        act = parse(
            args.image,
            provider=args.provider,
            model=args.model,
            act_type_hint=args.hint,
            act_language_hint=args.lang,
            context=args.context,
            output_mode=output_mode,
            validate=not args.no_validate,
        )
    except TabellioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "gedcom" and isinstance(act, Act):
        print(to_gedcom(act), end="")
    elif isinstance(act, Transcription):
        print(act.text)
    else:
        print(act.model_dump_json(indent=2, exclude_none=True))
    warnings = getattr(act, "warnings", [])
    if warnings:
        print(f"\n{len(warnings)} warning(s):", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
