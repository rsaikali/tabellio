from __future__ import annotations

from tabellio.schema import Act
from tabellio.validate import validate


def test_marriage_missing_bride():
    act = Act.model_validate(
        {
            "type": "marriage",
            "date": {"raw": "x", "iso": "1830-06-01", "confidence": 0.9},
            "persons": [{"role": "groom", "given": {"value": "Jean", "confidence": 0.9}}],
        }
    )
    validate(act)
    assert any("bride" in w for w in act.warnings)


def test_two_digit_year_flagged():
    act = Act.model_validate(
        {
            "type": "birth",
            "date": {"raw": "l'an 12", "iso": "12-01-01", "confidence": 0.9},
            "persons": [{"role": "subject"}],
        }
    )
    validate(act)
    assert any("2-digit year" in w for w in act.warnings)


def test_inferred_date_flagged():
    act = Act.model_validate(
        {
            "type": "death",
            "date": {
                "raw": "aujourd'hui",
                "iso": "1800-01-01",
                "confidence": 0.8,
                "inferred": True,
            },
            "persons": [{"role": "subject"}],
        }
    )
    validate(act)
    assert any("inferred" in w for w in act.warnings)


def test_low_confidence_flagged():
    act = Act.model_validate(
        {
            "type": "burial",
            "date": {"raw": "x", "iso": "1700-01-01", "confidence": 0.9},
            "persons": [
                {"role": "subject", "surname": {"value": "Flou", "raw": "Flou", "confidence": 0.2}}
            ],
        }
    )
    validate(act)
    assert any("low confidence" in w for w in act.warnings)


def test_clean_act_no_warnings():
    act = Act.model_validate(
        {
            "type": "baptism",
            "date": {"raw": "x", "iso": "1710-04-04", "confidence": 0.95},
            "persons": [
                {
                    "role": "subject",
                    "given": {"value": "Anne", "raw": "Anne", "confidence": 0.9},
                    "birth_date": {"raw": "ce jour", "iso": "1710-04-04", "confidence": 0.9},
                }
            ],
        }
    )
    validate(act)
    assert act.warnings == []


def test_baptism_without_birth_date_is_flagged():
    act = Act.model_validate(
        {
            "type": "baptism",
            "date": {"raw": "x", "iso": "1710-04-04", "confidence": 0.95},
            "persons": [{"role": "subject", "given": {"value": "Anne", "confidence": 0.9}}],
        }
    )
    validate(act)
    assert any("no birth date recorded" in w for w in act.warnings)


def test_burial_without_death_date_is_flagged():
    act = Act.model_validate(
        {
            "type": "burial",
            "date": {"raw": "x", "iso": "1710-04-04", "confidence": 0.95},
            "persons": [{"role": "subject", "given": {"value": "Anne", "confidence": 0.9}}],
        }
    )
    validate(act)
    assert any("no death date recorded" in w for w in act.warnings)


def test_birth_act_not_flagged_for_missing_birth_date():
    act = Act.model_validate(
        {
            "type": "birth",
            "date": {"raw": "x", "iso": "1710-04-04", "confidence": 0.95},
            "persons": [{"role": "subject", "given": {"value": "Anne", "confidence": 0.9}}],
        }
    )
    validate(act)
    assert act.warnings == []
