"""Pydantic v2 models for an extracted act.

Design rules (see CLAUDE.md):
- No silent resolution. Keep the original spelling in ``raw``.
- Anything not read stays ``None`` with a ``note`` -- never guessed.
- Every transcribed field carries its own ``confidence`` in [0, 1].
"""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ActType(StrEnum):
    BIRTH = "birth"
    BAPTISM = "baptism"
    MARRIAGE = "marriage"
    DEATH = "death"
    BURIAL = "burial"


class Role(StrEnum):
    SUBJECT = "subject"
    FATHER = "father"
    MOTHER = "mother"
    GROOM = "groom"
    BRIDE = "bride"
    GROOM_FATHER = "groom_father"
    GROOM_MOTHER = "groom_mother"
    BRIDE_FATHER = "bride_father"
    BRIDE_MOTHER = "bride_mother"
    WITNESS = "witness"
    GODPARENT = "godparent"
    OFFICIANT = "officiant"
    DECLARANT = "declarant"
    SPOUSE = "spouse"
    OTHER = "other"


class SourceHint(StrEnum):
    PARISH = "parish"
    CIVIL = "civil"
    UNKNOWN = "unknown"


class Cited(BaseModel, Generic[T]):
    """A single transcribed value plus its provenance.

    ``value`` is the normalised reading (``None`` when unreadable or ambiguous),
    ``raw`` is the text exactly as written on the act.
    """

    model_config = ConfigDict(extra="forbid")

    value: T | None = None
    raw: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    inferred: bool = False
    note: str | None = None


class GenDate(BaseModel):
    """A date cited on the act, spelling preserved."""

    model_config = ConfigDict(extra="forbid")

    raw: str | None = None
    iso: str | None = Field(
        default=None,
        description="Best-effort YYYY-MM-DD (or YYYY-MM / YYYY). None if not resolvable.",
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    inferred: bool = Field(
        default=False,
        description="True when the date is deduced (e.g. from age) rather than stated.",
    )
    note: str | None = None


class Person(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    given: Cited[str] | None = None
    surname: Cited[str] | None = None
    sex: Cited[str] | None = None
    age: Cited[str] | None = None
    occupation: Cited[str] | None = None
    residence: Cited[str] | None = None
    birth_date: GenDate | None = None
    birth_place: Cited[str] | None = None
    death_date: GenDate | None = None
    death_place: Cited[str] | None = None
    note: str | None = None


class Note(BaseModel):
    """Marginal notes, reading notes, and other free-form observations."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(description="e.g. 'margin', 'reading', 'occupation', 'other'")
    text: str
    person_ref: str | None = Field(
        default=None,
        description="Free-text pointer to a person in ``persons`` when relevant.",
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Act(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ActType
    date: GenDate
    place: Cited[str] | None = None
    persons: list[Person] = Field(default_factory=list)
    other: list[Note] = Field(default_factory=list)
    source_hint: SourceHint = SourceHint.UNKNOWN
    language: str | None = Field(
        default=None,
        description=(
            "Main language of the act as an ISO 639-1 code ('fr', 'la', 'de', ...). "
            "Metadata only -- free text is transcribed in the source language, never translated."
        ),
    )
    provider: str | None = None
    warnings: list[str] = Field(
        default_factory=list,
        description="Filled by tabellio.validate -- consistency and low-confidence flags.",
    )


# --- output_mode="simple" -------------------------------------------------------
# A deliberately bare projection: identity fields only. No raw spelling, no
# confidence, no inference flags, no notes, no warnings. Produced by a shorter
# prompt against its own schema, not derived from Act.


class PersonSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    given: str | None = None
    surname: str | None = None


class ActSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ActType
    date: str | None = Field(
        default=None,
        description="ISO YYYY-MM-DD (or YYYY-MM / YYYY), else null. No raw spelling.",
    )
    location: str | None = None
    persons: list[PersonSummary] = Field(default_factory=list)
