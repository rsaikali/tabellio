"""tabellio: image of a civil-registry / parish record -> validated structured JSON.

BYOK (bring your own key), provider-agnostic, no embedded model, no storage.
"""

from __future__ import annotations

from tabellio.core import parse
from tabellio.errors import (
    BackendError,
    BackendNotAvailable,
    ImageError,
    SchemaMismatch,
    TabellioError,
)
from tabellio.schema import Act, ActType, Cited, GenDate, Note, Person, Role

__version__ = "0.0.1"

__all__ = [
    "Act",
    "ActType",
    "BackendError",
    "BackendNotAvailable",
    "Cited",
    "GenDate",
    "ImageError",
    "Note",
    "Person",
    "Role",
    "SchemaMismatch",
    "TabellioError",
    "__version__",
    "parse",
]
