from __future__ import annotations

import io

import pytest

from tabellio.errors import ImageError
from tabellio.image import load_image, to_data_url


def test_load_bytes(png_bytes):
    data, mime = load_image(png_bytes)
    assert data == png_bytes
    assert mime == "image/png"


def test_load_path(tmp_path, png_bytes):
    p = tmp_path / "act.png"
    p.write_bytes(png_bytes)
    data, mime = load_image(str(p))
    assert (data, mime) == (png_bytes, "image/png")


def test_load_file_like(png_bytes):
    data, mime = load_image(io.BytesIO(png_bytes))
    assert (data, mime) == (png_bytes, "image/png")


def test_missing_file(tmp_path):
    with pytest.raises(ImageError):
        load_image(tmp_path / "nope.png")


def test_empty_image():
    with pytest.raises(ImageError):
        load_image(b"")


def test_unknown_format():
    with pytest.raises(ImageError):
        load_image(b"not an image at all")


def test_data_url(png_bytes):
    url = to_data_url(png_bytes, "image/png")
    assert url.startswith("data:image/png;base64,")
