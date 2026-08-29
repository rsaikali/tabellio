"""``python -m tabellio <image>`` -- quick manual check against one record.

The API key is read from the environment (see ``tabellio.parse``); it is never
taken as a CLI argument so it cannot land in shell history.
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from tabellio import parse
from tabellio.backends import available_backends
from tabellio.errors import TabellioError


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tabellio")
    ap.add_argument("image", help="path to an image of a single record")
    ap.add_argument("--backend", default="gemini", choices=available_backends())
    ap.add_argument("--model", default=None, help="override the backend default model")
    ap.add_argument(
        "--hint",
        default=None,
        choices=["birth", "baptism", "marriage", "death", "burial"],
        help="act type hint (still verified against the image)",
    )
    ap.add_argument("--no-validate", action="store_true", help="skip consistency rules")
    ap.add_argument("-v", "--verbose", action="store_true", help="show debug logs")
    args = ap.parse_args(argv)

    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.verbose else "WARNING")

    try:
        act = parse(
            args.image,
            backend=args.backend,
            act_type_hint=args.hint,
            model=args.model,
            validate=not args.no_validate,
        )
    except TabellioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(act.model_dump_json(indent=2, exclude_none=True))
    if act.warnings:
        print(f"\n{len(act.warnings)} warning(s):", file=sys.stderr)
        for w in act.warnings:
            print(f"  - {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
