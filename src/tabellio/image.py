"""Image normalisation: accept many input shapes, emit ``(bytes, mime)``.

No decoding, no deskew, no binarisation -- out of scope for v1 (see CLAUDE.md).
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import BinaryIO

from tabellio.errors import ImageError

ImageInput = str | Path | bytes | bytearray | BinaryIO

_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
)


def _sniff_mime(data: bytes) -> str:
    for magic, mime in _MAGIC:
        if data.startswith(magic):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ImageError("unrecognised image format (expected jpeg, png, tiff or webp)")


def load_image(image: ImageInput) -> tuple[bytes, str]:
    """Return ``(raw_bytes, mime_type)`` for any supported input shape."""
    if isinstance(image, str | Path):
        path = Path(image)
        if not path.is_file():
            raise ImageError(f"no such file: {path}")
        data = path.read_bytes()
    elif isinstance(image, bytes | bytearray):
        data = bytes(image)
    elif hasattr(image, "read"):
        data = image.read()
        if not isinstance(data, bytes | bytearray):
            raise ImageError("file-like object did not return bytes")
        data = bytes(data)
    else:
        raise ImageError(f"unsupported image input: {type(image)!r}")

    if not data:
        raise ImageError("image is empty")
    return data, _sniff_mime(data)


def to_data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


_JPEG_QUALITY_STEPS = (90, 80, 70, 60, 50, 40)
_MIN_LONG_EDGE = 1200  # below this a full-page act is usually unreadable


def fit_within(
    data: bytes, max_bytes: int, *, min_long_edge: int = _MIN_LONG_EDGE
) -> tuple[bytes, str]:
    """Re-encode ``data`` in memory so it is <= ``max_bytes``, as JPEG.

    Lowers JPEG quality first, then scales the pixels down, keeping the long
    edge >= ``min_long_edge``. The source file is never touched. Returns
    ``(bytes, "image/jpeg")``. Raises :class:`ImageError` if Pillow is missing
    or the target cannot be met.
    """
    try:
        from io import BytesIO

        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on install extras
        raise ImageError(
            "resizing needs Pillow: pip install 'tabellio[resize]' (or 'tabellio[nim]')"
        ) from exc

    if len(data) <= max_bytes:
        return data, _sniff_mime(data)

    try:
        img = Image.open(BytesIO(data))
        img.load()
    except OSError as exc:
        raise ImageError(f"cannot decode image for resizing: {exc}") from exc
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    def encode(im: Image.Image, quality: int) -> bytes:
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

    for quality in _JPEG_QUALITY_STEPS:
        out = encode(img, quality)
        if len(out) <= max_bytes:
            return out, "image/jpeg"

    while max(img.size) > min_long_edge:
        img = img.resize((max(1, int(img.width * 0.8)), max(1, int(img.height * 0.8))))
        for quality in (65, 50, 35):
            out = encode(img, quality)
            if len(out) <= max_bytes:
                return out, "image/jpeg"

    out = encode(img, 30)
    if len(out) > max_bytes:
        raise ImageError(
            f"cannot shrink image under {max_bytes} bytes without going below "
            f"{min_long_edge}px on the long edge (got {len(out)} bytes)"
        )
    return out, "image/jpeg"
