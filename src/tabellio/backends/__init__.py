"""Provider adapters. Nothing here is imported until a backend is requested."""

from __future__ import annotations

from tabellio.backends.base import Backend, available_backends, get_backend

__all__ = ["Backend", "available_backends", "get_backend"]
