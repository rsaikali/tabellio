"""Exception hierarchy for tabellio."""

from __future__ import annotations


class TabellioError(Exception):
    """Base class for every error raised by this library."""


class ImageError(TabellioError):
    """The supplied image could not be read or its format is unsupported."""


class ProviderNotAvailable(TabellioError):
    """A provider was requested but its optional SDK is not installed."""


class ProviderError(TabellioError):
    """The provider call failed or returned an unusable response."""


class SchemaMismatch(TabellioError):
    """The model output could not be validated against the Act schema."""

    def __init__(self, message: str, *, raw: object = None) -> None:
        super().__init__(message)
        self.raw = raw
