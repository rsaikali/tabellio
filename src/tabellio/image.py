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
