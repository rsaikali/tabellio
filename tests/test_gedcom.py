from __future__ import annotations

import pytest

from tabellio import to_gedcom
from tabellio.schema import Act

BAPTISM = {
    "type": "baptism",
    "date": {"raw": "le 12 may 1703", "iso": "1703-05-12", "confidence": 0.9},
    "place": {"value": "Villeneuve-sur-Exemple", "raw": "Villeneufve", "confidence": 0.7},
    "language": "fr",
    "source_hint": "parish",
    "persons": [
        {
            "role": "subject",
            "given": {"value": "Jeanne", "confidence": 0.95},
            "surname": {"value": "Dupont", "confidence": 0.8},
            "sex": {"value": "female", "confidence": 0.6},
            "birth_date": {
                "raw": "nee la veille",
                "iso": "1703-05-11",
                "qualifier": "calculated",
                "confidence": 0.8,
                "note": "act says 'nee la veille'",
            },
        },
        {
            "role": "father",
            "given": {"value": "Pierre", "confidence": 0.9},
            "name_particle": {"value": "de", "confidence": 0.9},
            "surname": {"value": "Fontaine", "confidence": 0.8},
            "occupation": {"value": "laboureur", "confidence": 0.6},
        },
        {"role": "mother", "given": {"value": "Marie", "confidence": 0.9}},
        {
            "role": "godparent",
            "given": {"value": "Anne", "confidence": 0.8},
            "surname": {"value": "Roy", "confidence": 0.7},
        },
    ],
    "other": [{"kind": "margin", "text": "baptisee le mesme jour", "confidence": 0.7}],
}

MARRIAGE = {
    "type": "marriage",
    "date": {"raw": "le 26 septembre 1699", "iso": "1699-09-26", "confidence": 0.9},
    "place": {"value": "Vigneux-de-Bretagne", "confidence": 0.8},
    "persons": [
        {
            "role": "groom",
            "given": {"value": "Julien", "confidence": 0.9},
            "surname": {"value": "Rousset", "confidence": 0.85},
        },
        {
            "role": "bride",
            "given": {"value": "Perrine", "confidence": 0.9},
            "surname": {"value": "Deniau", "confidence": 0.85},
        },
        {
            "role": "witness",
            "given": {"value": "Guillaume", "confidence": 0.7},
            "surname": {"value": "Bahuaud", "confidence": 0.6},
        },
    ],
}

BURIAL = {
    "type": "burial",
    "date": {"raw": "le 22 decembre 1757", "iso": "1757-12-22", "confidence": 0.85},
    "persons": [
        {
            "role": "subject",
            "given": {"value": "Joseph", "confidence": 0.8},
            "surname": {"value": "Commal", "confidence": 0.6},
            "age": {"value": "60", "raw": "environ soixante ans", "confidence": 0.5},
            "death_date": {
                "raw": "decede la veille",
                "iso": "1757-12-21",
                "qualifier": "calculated",
                "confidence": 0.7,
                "note": "act says 'la veille'",
            },
        }
    ],
}


def _lines(text: str) -> list[tuple[int, str]]:
    out = []
    for ln in text.splitlines():
        level, rest = ln.split(" ", 1)
        out.append((int(level), rest))
    return out


def _assert_well_formed(ged: str) -> None:
    assert ged.startswith("0 HEAD\n")
    assert ged.rstrip().endswith("0 TRLR")
    assert "2 VERS 7.0" in ged
    assert "@@" not in ged  # no double-escaped pointers
    prev = -1
    for level, _ in _lines(ged):
        assert level <= prev + 1, f"level jumps from {prev} to {level}"
        prev = level
    _assert_gedcom7_valid(ged)


def _assert_gedcom7_valid(ged: str) -> None:
    gedcom7 = pytest.importorskip("gedcom7")
    errors = gedcom7.validate(gedcom7.loads(ged))
    assert not errors, f"GEDCOM 7 conformance errors: {errors}"


def test_baptism_structure():
    ged = to_gedcom(Act.model_validate(BAPTISM))
    _assert_well_formed(ged)
    assert "0 @S1@ SOUR" in ged
    assert ged.count("\n0 @I") == 4  # one INDI per person
    assert "0 @F1@ FAM" in ged
    assert "1 BAPM" in ged
    assert "2 DATE 12 MAY 1703" in ged
    # the subject's real birth becomes its own event, calculated
    assert "1 BIRT" in ged
    assert "2 DATE CAL 11 MAY 1703" in ged
    # godparent -> ASSO on the baptism event
    assert "3 ROLE GODP" in ged
    # particle
    assert "1 NAME Pierre /de Fontaine/" in ged
    assert "2 SPFX de" in ged
    # child linked to the family
    assert "1 FAMC @F1@" in ged
    assert "1 CHIL @I1@" in ged
    assert "1 LANG fr" in ged


def test_marriage_structure():
    ged = to_gedcom(Act.model_validate(MARRIAGE))
    _assert_well_formed(ged)
    assert "0 @F1@ FAM" in ged
    assert "1 HUSB @I1@" in ged and "1 WIFE @I2@" in ged
    assert "1 MARR" in ged
    assert "2 DATE 26 SEP 1699" in ged
    assert ged.count("1 FAMS @F1@") == 2
    assert "3 ROLE WITN" in ged


def test_burial_structure():
    ged = to_gedcom(Act.model_validate(BURIAL))
    _assert_well_formed(ged)
    assert "1 BURI" in ged
    assert "1 DEAT" in ged
    assert "2 DATE CAL 21 DEC 1757" in ged
    assert "2 DATE 22 DEC 1757" in ged  # the burial itself
    assert 'age stated: "environ soixante ans"' not in ged  # numeric -> AGE
    assert "2 AGE 60y" in ged
    # no FAM: burial names no couple or parent
    assert "0 @F1@ FAM" not in ged


def test_partial_date_and_no_iso():
    act = Act.model_validate(
        {
            "type": "death",
            "date": {"raw": "en 1812", "iso": "1812", "confidence": 0.7},
            "persons": [{"role": "subject", "given": {"value": "X", "confidence": 0.5}}],
        }
    )
    ged = to_gedcom(act)
    _assert_well_formed(ged)
    assert "2 DATE 1812" in ged


def test_unreadable_person_name():
    act = Act.model_validate(
        {
            "type": "death",
            "date": {"raw": "x", "iso": "1800-01-01", "confidence": 0.9},
            "persons": [{"role": "subject", "surname": {"value": None, "note": "illegible"}}],
        }
    )
    ged = to_gedcom(act)
    _assert_well_formed(ged)
    assert "1 NAME /Unknown/" in ged


@pytest.mark.parametrize("act_type", ["birth", "baptism", "marriage", "death", "burial"])
def test_every_act_type_serialises(act_type):
    act = Act.model_validate(
        {
            "type": act_type,
            "date": {"raw": "x", "iso": "1800-06-15", "confidence": 0.8},
            "persons": [
                {
                    "role": "groom" if act_type == "marriage" else "subject",
                    "given": {"value": "A", "confidence": 0.8},
                },
                *(
                    [{"role": "bride", "given": {"value": "B", "confidence": 0.8}}]
                    if act_type == "marriage"
                    else []
                ),
            ],
        }
    )
    _assert_well_formed(to_gedcom(act))
