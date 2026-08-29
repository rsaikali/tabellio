"""GEDCOM 7.0 serialisation of an extracted :class:`~tabellio.schema.Act`.

``to_gedcom(act)`` returns a complete, importable GEDCOM 7.0 document: a ``HEAD``,
one ``SOUR`` record for the act, one ``INDI`` per person the act names, a ``FAM``
when the act states a couple or a parent-child link, and ``TRLR``.

It transcribes what the act says. It does not build or merge a family tree --
that is the genealogist's software's job on import. Importing two acts about the
same person yields two ``INDI`` records; deduplication happens in the tree, not
here.

Mapping notes:
- ``act.date`` is the date of the ceremony / registration; a subject's real
  birth or death (``Person.birth_date`` / ``death_date``) becomes its own
  ``BIRT`` / ``DEAT`` event.
- ``GenDate.qualifier`` -> GEDCOM date prefix (``ABT``/``BEF``/``AFT``/``CAL``).
- ``GenDate.iso`` is always proleptic-Gregorian, so dates are emitted as
  ``GREGORIAN``; a non-Gregorian ``calendar`` and the ``raw`` wording are kept
  in a ``PHRASE`` / ``NOTE``.
- per-field ``confidence`` -> ``QUAY`` (0-3) on the source citation.
- witnesses, godparents and the officiant -> ``ASSO`` + ``ROLE`` on the event.
"""

from __future__ import annotations

import datetime as _dt

from tabellio.schema import Act, ActType, Calendar, DateQualifier, GenDate, Person, Role

_MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

_QUALIFIER_PREFIX = {
    DateQualifier.EXACT: "",
    DateQualifier.ABOUT: "ABT ",
    DateQualifier.BEFORE: "BEF ",
    DateQualifier.AFTER: "AFT ",
    DateQualifier.CALCULATED: "CAL ",
    DateQualifier.BETWEEN: "ABT ",  # single value; the bounds live in the note
}

_PRIMARY_EVENT = {
    ActType.BIRTH: "BIRT",
    ActType.BAPTISM: "BAPM",
    ActType.DEATH: "DEAT",
    ActType.BURIAL: "BURI",
    ActType.MARRIAGE: "MARR",
}

# Non-principal roles: attached to the event via ASSO. value = GEDCOM ROLE, or
# (OTHER, phrase).
_ASSO_ROLE: dict[Role, str | tuple[str, str]] = {
    Role.WITNESS: "WITN",
    Role.GODPARENT: "GODP",
    Role.OFFICIANT: "OFFICIATOR",
    Role.DECLARANT: ("OTHER", "declarant"),
    Role.GROOM_FATHER: ("OTHER", "groom's father"),
    Role.GROOM_MOTHER: ("OTHER", "groom's mother"),
    Role.BRIDE_FATHER: ("OTHER", "bride's father"),
    Role.BRIDE_MOTHER: ("OTHER", "bride's mother"),
    Role.SPOUSE: ("OTHER", "spouse named in the act"),
    Role.OTHER: ("OTHER", "unspecified"),
}

_MALE_ROLES = {Role.FATHER, Role.GROOM, Role.GROOM_FATHER, Role.BRIDE_FATHER}
_FEMALE_ROLES = {Role.MOTHER, Role.BRIDE, Role.GROOM_MOTHER, Role.BRIDE_MOTHER}


def _val(cited: object) -> str | None:
    v = getattr(cited, "value", None) if cited is not None else None
    return v if isinstance(v, str) and v.strip() else None


def _emit(out: list[str], level: int, tag: str, value: str = "") -> None:
    """Emit a line whose value is literal text (leading '@' doubled, newlines -> CONT)."""
    if value == "":
        out.append(f"{level} {tag}")
        return
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    head = lines[0]
    if head.startswith("@") and not head.startswith("@#"):
        head = "@" + head
    out.append(f"{level} {tag} {head}")
    for cont in lines[1:]:
        out.append(f"{level + 1} CONT {cont}")


def _ptr(out: list[str], level: int, tag: str, xref: str) -> None:
    """Emit a line whose value is an xref pointer (e.g. ``2 SOUR @S1@``)."""
    out.append(f"{level} {tag} {xref}")


def _fmt_date(d: GenDate | None) -> str | None:
    if d is None or d.iso is None:
        return None
    bits = d.iso.split("-")
    try:
        if len(bits) == 3:
            core = f"{int(bits[2])} {_MONTHS[int(bits[1]) - 1]} {int(bits[0])}"
        elif len(bits) == 2:
            core = f"{_MONTHS[int(bits[1]) - 1]} {int(bits[0])}"
        else:
            core = str(int(bits[0]))
    except (ValueError, IndexError):
        return None
    return _QUALIFIER_PREFIX.get(d.qualifier, "") + core


def _quay(confidence: float) -> str | None:
    if confidence <= 0.0:
        return None
    if confidence >= 0.85:
        return "3"
    if confidence >= 0.6:
        return "2"
    if confidence >= 0.3:
        return "1"
    return "0"


def _sex(p: Person) -> str:
    v = (_val(p.sex) or "").strip().lower()
    if v in ("f", "female", "femme", "fille", "femina", "mulier"):
        return "F"
    if v in ("m", "male", "homme", "garcon", "garçon", "vir", "masculus"):
        return "M"
    if p.role in _MALE_ROLES:
        return "M"
    if p.role in _FEMALE_ROLES:
        return "F"
    return "U"


def _person_notes(p: Person) -> list[str]:
    notes: list[str] = []
    if p.note:
        notes.append(p.note)
    for label, cited in (
        ("given name", p.given),
        ("surname", p.surname),
        ("occupation", p.occupation),
        ("residence", p.residence),
    ):
        n = getattr(cited, "note", None) if cited is not None else None
        if n:
            notes.append(f"{label}: {n}")
    if _val(p.given) is None and _val(p.surname) is None and not notes:
        notes.append("name not legible on the act")
    return notes


def _emit_name(out: list[str], p: Person) -> None:
    given = _val(p.given)
    particle = _val(p.name_particle)
    surname = _val(p.surname)
    suffix = _val(p.name_suffix)
    slashed = " ".join(x for x in (particle, surname) if x)
    payload = " ".join(
        x for x in (given or "", f"/{slashed}/" if slashed else "", suffix or "") if x
    ).strip()
    _emit(out, 1, "NAME", payload or "/Unknown/")
    if given:
        _emit(out, 2, "GIVN", given)
    if surname:
        _emit(out, 2, "SURN", surname)
    if particle:
        _emit(out, 2, "SPFX", particle)
    if suffix:
        _emit(out, 2, "NSFX", suffix)


def _emit_event(
    out: list[str],
    level: int,
    tag: str,
    date: GenDate | None,
    place: object,
    *,
    age: object = None,
    src: str,
    assos: list[tuple[str, str | tuple[str, str]]] | None = None,
) -> None:
    out.append(f"{level} {tag}")
    formatted = _fmt_date(date)
    if formatted:
        _emit(out, level + 1, "DATE", formatted)
        if date and date.raw:
            _emit(out, level + 2, "PHRASE", date.raw)
    if date and date.note:
        _emit(out, level + 1, "NOTE", date.note)
    if date and date.calendar is not Calendar.GREGORIAN:
        _emit(out, level + 1, "NOTE", f"original calendar: {date.calendar}")
    place_val = _val(place)
    if place_val:
        _emit(out, level + 1, "PLAC", place_val)
    age_val = _val(age)
    if age_val:
        if age_val.isdigit():
            _emit(out, level + 1, "AGE", f"{age_val}y")
        else:
            _emit(out, level + 1, "NOTE", f'age stated: "{age_val}"')
    for xref, role in assos or []:
        _ptr(out, level + 1, "ASSO", xref)
        if isinstance(role, tuple):
            _emit(out, level + 2, "ROLE", role[0])
            _emit(out, level + 3, "PHRASE", role[1])
        else:
            _emit(out, level + 2, "ROLE", role)
    _ptr(out, level + 1, "SOUR", src)
    quay = _quay(date.confidence if date else 0.0)
    if quay is not None:
        _emit(out, level + 2, "QUAY", quay)


def _source_title(act: Act) -> str:
    subject = next((p for p in act.persons if p.role is Role.SUBJECT), None)
    who = None
    if subject is not None:
        who = " ".join(filter(None, [_val(subject.given), _val(subject.surname)])) or None
    elif act.type is ActType.MARRIAGE:
        g = next((p for p in act.persons if p.role is Role.GROOM), None)
        b = next((p for p in act.persons if p.role is Role.BRIDE), None)
        names = [
            " ".join(filter(None, [_val(x.given), _val(x.surname)]))
            for x in (g, b)
            if x is not None
        ]
        who = " & ".join(n for n in names if n) or None
    year = act.date.iso.split("-")[0] if act.date and act.date.iso else None
    parts = [act.type.capitalize()]
    if who:
        parts.append(f"of {who}")
    if year:
        parts.append(f"({year})")
    return " ".join(parts)


def to_gedcom(act: Act) -> str:
    """Serialise ``act`` as a complete GEDCOM 7.0 document."""
    from tabellio import __version__

    persons = act.persons
    xref = {i: f"@I{i + 1}@" for i in range(len(persons))}
    src = "@S1@"

    def first(role: Role) -> int | None:
        return next((i for i, p in enumerate(persons) if p.role is role), None)

    subject = first(Role.SUBJECT)
    father, mother = first(Role.FATHER), first(Role.MOTHER)
    groom, bride = first(Role.GROOM), first(Role.BRIDE)

    is_marriage = act.type is ActType.MARRIAGE
    husb = groom if groom is not None else father
    wife = bride if bride is not None else mother
    child = subject if (father is not None or mother is not None) else None
    fam_needed = is_marriage or father is not None or mother is not None
    fam = "@F1@" if fam_needed else None
    spouses = {i for i in (husb, wife) if i is not None} if is_marriage else set()

    # people attached to the primary event but not principals
    principals = {subject, father, mother, groom, bride}
    assos = [
        (xref[i], _ASSO_ROLE[p.role])
        for i, p in enumerate(persons)
        if i not in principals and p.role in _ASSO_ROLE
    ]

    today = _dt.date.today()
    out: list[str] = [
        "0 HEAD",
        "1 GEDC",
        "2 VERS 7.0",
        "1 SOUR tabellio",
        f"2 VERS {__version__}",
        f"1 DATE {today.day} {_MONTHS[today.month - 1]} {today.year}",
    ]
    if act.language:
        _emit(out, 1, "LANG", act.language)

    # --- SOUR record ---------------------------------------------------------
    out.append(f"0 {src} SOUR")
    _emit(out, 1, "TITL", _source_title(act))
    if act.source_hint and str(act.source_hint) != "unknown":
        _emit(out, 1, "NOTE", f"register type: {act.source_hint}")
    if act.date and act.date.raw:
        _emit(out, 1, "NOTE", f'act dated: "{act.date.raw}"')
    for n in act.other:
        _emit(out, 1, "NOTE", f"[{n.kind}] {n.text}")

    # --- INDI records ------------------------------------------------------
    for i, p in enumerate(persons):
        out.append(f"0 {xref[i]} INDI")
        _emit_name(out, p)
        _emit(out, 1, "SEX", _sex(p))
        occ = _val(p.occupation)
        if occ:
            _emit(out, 1, "OCCU", occ)
        res = _val(p.residence)
        if res:
            _emit(out, 1, "RESI")
            _emit(out, 2, "PLAC", res)

        is_subject = i == subject
        if is_subject and not is_marriage:
            tag = _PRIMARY_EVENT[act.type]
            ceremony_date = (
                act.date
                if act.type in (ActType.BAPTISM, ActType.BURIAL)
                else (act.date if act.date and act.date.iso else p.birth_date or p.death_date)
            )
            _emit_event(
                out,
                1,
                tag,
                ceremony_date,
                act.place,
                age=p.age if act.type in (ActType.DEATH, ActType.BURIAL) else None,
                src=src,
                assos=assos,
            )

        # life-event dates carried on the person (subject's real birth for a
        # baptism, a parent's cited birth, etc.)
        if p.birth_date is not None and not (is_subject and act.type is ActType.BIRTH):
            _emit_event(out, 1, "BIRT", p.birth_date, p.birth_place, src=src)
        elif p.birth_place is not None and _val(p.birth_place):
            _emit_event(out, 1, "BIRT", None, p.birth_place, src=src)
        if p.death_date is not None and not (is_subject and act.type is ActType.DEATH):
            _emit_event(out, 1, "DEAT", p.death_date, p.death_place, src=src)
        elif p.death_place is not None and _val(p.death_place):
            _emit_event(out, 1, "DEAT", None, p.death_place, src=src)

        if fam is not None:
            if i in spouses or (is_marriage and i in (husb, wife)):
                _ptr(out, 1, "FAMS", fam)
            elif i == child:
                _ptr(out, 1, "FAMC", fam)

        for note in _person_notes(p):
            _emit(out, 1, "NOTE", note)

    # --- FAM record --------------------------------------------------------
    if fam is not None:
        out.append(f"0 {fam} FAM")
        if husb is not None:
            _ptr(out, 1, "HUSB", xref[husb])
        if wife is not None:
            _ptr(out, 1, "WIFE", xref[wife])
        if child is not None:
            _ptr(out, 1, "CHIL", xref[child])
        if is_marriage:
            _emit_event(out, 1, "MARR", act.date, act.place, src=src, assos=assos)

    out.append("0 TRLR")
    return "\n".join(out) + "\n"
