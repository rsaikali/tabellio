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


def _page_jpeg(w: int, h: int) -> bytes:
    """A scan-like image: mostly white with sparse dark marks (compresses well)."""
    import random
    from io import BytesIO

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    rng = random.Random(0)
    for _ in range(4000):
        x, y = rng.randint(0, w - 20), rng.randint(0, h - 8)
        draw.line([(x, y), (x + rng.randint(4, 18), y + rng.randint(-3, 3))], fill="black", width=2)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_fit_within_noop_when_small(png_bytes):
    from tabellio.image import fit_within

    out, mime = fit_within(png_bytes, 10_000_000)
    assert out == png_bytes and mime == "image/png"


def test_fit_within_shrinks_to_budget():
    from tabellio.image import fit_within

    big = _page_jpeg(3000, 2000)
    assert len(big) > 180_000
    out, mime = fit_within(big, 180_000)
    assert len(out) <= 180_000
    assert mime == "image/jpeg"
    assert out.startswith(b"\xff\xd8\xff")


def test_fit_within_rejects_undecodable():
    from tabellio.errors import ImageError
    from tabellio.image import fit_within

    with pytest.raises(ImageError):
        fit_within(b"not an image" * 20_000, 1000)
