"""Post-extraction consistency rules.

These never rewrite the model output. They only append human-readable strings
to ``act.warnings`` so the caller can surface them.
"""

from __future__ import annotations

from tabellio.schema import Act, ActType, GenDate, Role

LOW_CONFIDENCE = 0.5

_EXPECTED_ROLES: dict[ActType, set[Role]] = {
    ActType.BIRTH: {Role.SUBJECT},
    ActType.BAPTISM: {Role.SUBJECT},
    ActType.DEATH: {Role.SUBJECT},
    ActType.BURIAL: {Role.SUBJECT},
    ActType.MARRIAGE: {Role.GROOM, Role.BRIDE},
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


def _check_inferred_dates(act: Act, out: list[str]) -> None:
    if act.date.inferred:
        out.append("act date is marked inferred, not stated on the record")
    for p in act.persons:
        for d, kind in ((p.birth_date, "birth"), (p.death_date, "death")):
            if d is not None and d.inferred:
                name = " ".join(filter(None, [_val(p.given), _val(p.surname)])) or p.role
                out.append(f"{kind} date for {name} is inferred")


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
    _check_inferred_dates(act, warnings)
    _check_low_confidence(act, warnings)
    act.warnings = warnings
    return act
