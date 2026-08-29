from __future__ import annotations

import pytest
from pydantic import ValidationError

from tabellio.schema import Act, Cited, Person, Role


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
    assert act.prompt_version is None
