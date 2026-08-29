"""Post-extraction consistency rules.

These never rewrite the model output. They only append human-readable strings
to ``act.warnings`` so the caller can surface them.
"""

from __future__ import annotations

from tabellio.schema import Act, ActType, DateQualifier, GenDate, Role

LOW_CONFIDENCE = 0.5

_EXPECTED_ROLES: dict[ActType, set[Role]] = {
    ActType.BIRTH: {Role.SUBJECT},
    ActType.BAPTISM: {Role.SUBJECT},
    ActType.DEATH: {Role.SUBJECT},
    ActType.BURIAL: {Role.SUBJECT},
    ActType.MARRIAGE: {Role.GROOM, Role.BRIDE},
}

#: For these act types the recorded event usually predates the act; the real
#: date belongs on the subject, not (only) on ``act.date``.
_EVENT_DATE_FIELD: dict[ActType, tuple[str, str]] = {
    ActType.BAPTISM: ("birth_date", "birth"),
    ActType.BURIAL: ("death_date", "death"),
}


def _check_roles(act: Act, out: list[str]) -> None:
    present = {p.role for p in act.persons}
    for role in _EXPECTED_ROLES.get(act.type, set()):
        if role not in present:
            out.append(f"{act.type} act has no person with role '{role}'")


def _check_two_digit_year(d: GenDate | None, label: str, out: list[str]) -> None:
    if d is None or d.iso is None:
        return
    year_part = d.iso.split("-", 1)[0]
    if year_part.isdigit() and len(year_part) < 4:
        out.append(
            f"{label}: year '{year_part}' looks like a 2-digit year expanded without evidence"
        )


def _check_date_qualifiers(act: Act, out: list[str]) -> None:
    def check(d: GenDate | None, label: str) -> None:
        if d is None or d.qualifier is DateQualifier.EXACT:
            return
        if d.qualifier is DateQualifier.CALCULATED:
            out.append(f"{label} is calculated, not stated on the act")
        if d.note is None:
            out.append(f"{label} is '{d.qualifier}' but carries no explanatory note")

    check(act.date, "act date")
    for p in act.persons:
        name = " ".join(filter(None, [_val(p.given), _val(p.surname)])) or p.role
        check(p.birth_date, f"birth date for {name}")
        check(p.death_date, f"death date for {name}")


def _check_event_date_captured(act: Act, out: list[str]) -> None:
    field_kind = _EVENT_DATE_FIELD.get(act.type)
    if field_kind is None:
        return
    field, kind = field_kind
    subject = next((p for p in act.persons if p.role is Role.SUBJECT), None)
    if subject is None:
        return  # already flagged by _check_roles
    d = getattr(subject, field)
    if d is None or (d.raw is None and d.iso is None):
        out.append(
            f"{act.type} act: no {kind} date recorded for the subject "
            f"(check whether the act states or implies one)"
        )


def _check_low_confidence(act: Act, out: list[str]) -> None:
    if act.date.raw and act.date.confidence < LOW_CONFIDENCE:
        out.append(f"low confidence on act date ({act.date.confidence:.2f})")
    for p in act.persons:
        for field in ("given", "surname", "occupation", "residence"):
            c = getattr(p, field)
            if c is not None and c.raw and c.confidence < LOW_CONFIDENCE:
                out.append(f"low confidence on {p.role}.{field} ('{c.raw}', {c.confidence:.2f})")


def _val(c: object) -> str | None:
    return getattr(c, "value", None) if c is not None else None


def validate(act: Act) -> Act:
    """Return ``act`` with ``warnings`` populated. Mutates and returns in place."""
    warnings: list[str] = []
    _check_roles(act, warnings)
    _check_two_digit_year(act.date, "act date", warnings)
    for p in act.persons:
        _check_two_digit_year(p.birth_date, f"{p.role} birth date", warnings)
        _check_two_digit_year(p.death_date, f"{p.role} death date", warnings)
    _check_date_qualifiers(act, warnings)
    _check_event_date_captured(act, warnings)
    _check_low_confidence(act, warnings)
    act.warnings = warnings
    return act
