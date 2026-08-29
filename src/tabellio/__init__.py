"""tabellio: image of a civil-registry / parish record -> validated structured JSON.

BYOK (bring your own key), provider-agnostic, no embedded model, no storage.
"""

from __future__ import annotations

from tabellio.core import parse
from tabellio.errors import (
    ImageError,
    ProviderError,
    ProviderNotAvailable,
    SchemaMismatch,
    TabellioError,
)
from tabellio.schema import Act, ActType, Cited, GenDate, Note, Person, Role

__version__ = "0.0.1"

__all__ = [
    "Act",
    "ActType",
    "Cited",
    "GenDate",
    "ImageError",
    "Note",
    "Person",
    "ProviderError",
    "ProviderNotAvailable",
    "Role",
    "SchemaMismatch",
    "TabellioError",
    "__version__",
    "parse",
]
