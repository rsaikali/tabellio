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
from tabellio.schema import (
    Act,
    ActSummary,
    ActType,
    Cited,
    GenDate,
    Note,
    Person,
    PersonSummary,
    Role,
)

__version__ = "0.0.1"

__all__ = [
    "Act",
    "ActSummary",
    "ActType",
    "Cited",
    "GenDate",
    "ImageError",
    "Note",
    "Person",
    "PersonSummary",
    "ProviderError",
    "ProviderNotAvailable",
    "Role",
    "SchemaMismatch",
    "TabellioError",
    "__version__",
    "parse",
]
