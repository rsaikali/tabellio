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
from tabellio.gedcom import to_gedcom
from tabellio.schema import (
    Act,
    ActSummary,
    ActType,
    Calendar,
    Cited,
    DateQualifier,
    GenDate,
    Note,
    Person,
    PersonSummary,
    Role,
    Transcription,
)

__version__ = "0.0.1"

__all__ = [
    "Act",
    "ActSummary",
    "ActType",
    "Calendar",
    "Cited",
    "DateQualifier",
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
    "Transcription",
    "__version__",
    "parse",
    "to_gedcom",
]
