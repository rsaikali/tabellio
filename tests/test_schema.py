from __future__ import annotations

import pytest
from pydantic import ValidationError

from tabellio.schema import Act, ActSummary, Cited, Person, Role


def test_act_roundtrip(fictional_act):
    act = Act.model_validate(fictional_act)
    assert act.type == "death"
    assert act.date.iso == "1812-01-03"
    assert act.persons[0].role is Role.SUBJECT
    again = Act.model_validate(act.model_dump())
    assert again == act


def test_cited_generic():
    c = Cited[str].model_validate({"value": "Marie", "raw": "Marye", "confidence": 0.8})
    assert c.value == "Marie" and c.raw == "Marye"
    assert c.inferred is False


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        Cited[str].model_validate({"confidence": 1.5})


def test_extra_forbidden():
    with pytest.raises(ValidationError):
        Person.model_validate({"role": "witness", "middle_name": "x"})


def test_defaults(fictional_act):
    act = Act.model_validate(fictional_act)
    assert act.warnings == []
    assert act.provider is None


def test_act_language_field(fictional_act):
    assert Act.model_validate(fictional_act).language is None
    latin = {**fictional_act, "language": "la"}
    assert Act.model_validate(latin).language == "la"


def test_act_transcription_field(fictional_act):
    assert Act.model_validate(fictional_act).transcription is None
    text = "L'an 1812, le 3 janvier, [?] est decede...\nsecond line."
    act = Act.model_validate({**fictional_act, "transcription": text})
    assert act.transcription == text


def test_act_summary(fictional_summary):
    s = ActSummary.model_validate(fictional_summary)
    assert s.type == "death"
    assert s.date == "1812-01-03"
    assert s.persons[0].role is Role.SUBJECT
    assert set(s.model_dump()) == {"type", "date", "location", "persons", "transcription"}
    assert s.transcription.startswith("L'an 1812")


def test_act_summary_forbids_full_fields():
    with pytest.raises(ValidationError):
        ActSummary.model_validate({"type": "birth", "date": {"raw": "x"}})
