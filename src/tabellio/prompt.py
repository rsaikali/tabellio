"""The extraction prompts and few-shot examples, versioned.

Two output modes, each with its own system prompt, few-shot and target schema:

- ``full``  -> :class:`tabellio.schema.Act` (raw spelling, confidence, notes).
- ``simple`` -> :class:`tabellio.schema.ActSummary` (identity fields only).

Bump ``PROMPT_VERSION`` whenever any wording changes so extractions stay
traceable to the instructions that produced them.
"""

from __future__ import annotations

import json

from tabellio.schema import Act, ActSummary

PROMPT_VERSION = "1"

_FULL_SYSTEM = """\
You are a palaeographer transcribing a single French civil-registry or parish
record from an image. Produce a strict JSON object matching the provided schema.

Rules:
- Transcribe, do not interpret. Never invent a name, date, place or fact that is
  not legible in the image.
- Keep the original spelling in every `raw` field, including archaic forms,
  abbreviations and diacritics as written.
- For each transcribed field give a `confidence` between 0 and 1 reflecting how
  sure you are of the reading.
- A date deduced (for instance from a stated age) must have `inferred: true` and
  a `note` explaining the deduction.
- If a field cannot be read, leave it null and add a short `note`. Do not guess.
- `source_hint`: "parish" for religious registers, "civil" for etat civil,
  "unknown" if you cannot tell.
- Output JSON only. No prose, no markdown fences.
"""

_SIMPLE_SYSTEM = """\
You are a palaeographer transcribing a single French civil-registry or parish
record from an image. Return a strict JSON object with EXACTLY these keys:

- "type": one of birth, baptism, marriage, death, burial
- "date": the date of the act as ISO "YYYY-MM-DD" (or "YYYY-MM" / "YYYY" if only
  that is legible), else null
- "location": the town or parish, else null
- "persons": array of objects {"role", "given", "surname"} where role is one of
  subject, father, mother, groom, bride, witness, godparent, officiant,
  declarant, spouse, other

Transcribe only what is legible; use null for anything you cannot read. Do not
guess, do not explain. No raw spelling, no confidence, no notes, no extra keys.
Output JSON only. No prose, no markdown fences.
"""

_FULL_EXAMPLE = {
    "type": "baptism",
    "date": {
        "raw": "le douziesme jour de may mil sept cens trois",
        "iso": "1703-05-12",
        "confidence": 0.9,
    },
    "place": {"value": "Villeneuve-sur-Exemple", "raw": "Villeneufve", "confidence": 0.7},
    "persons": [
        {
            "role": "subject",
            "given": {"value": "Jeanne", "raw": "Jeanne", "confidence": 0.95},
            "surname": {"value": "Dupont", "raw": "Dupont", "confidence": 0.8},
        },
        {
            "role": "father",
            "given": {"value": "Pierre", "raw": "Pierre", "confidence": 0.9},
            "surname": {"value": "Dupont", "raw": "Dupont", "confidence": 0.8},
            "occupation": {"value": "laboureur", "raw": "laboureur", "confidence": 0.6},
        },
        {
            "role": "mother",
            "given": {"value": "Marie", "raw": "Marie", "confidence": 0.9},
            "surname": {
                "value": None,
                "raw": None,
                "confidence": 0.0,
                "note": "maiden name not legible",
            },
        },
    ],
    "other": [
        {"kind": "margin", "text": "baptisee le mesme jour", "confidence": 0.7},
    ],
    "source_hint": "parish",
}

_SIMPLE_EXAMPLE = {
    "type": "baptism",
    "date": "1703-05-12",
    "location": "Villeneuve-sur-Exemple",
    "persons": [
        {"role": "subject", "given": "Jeanne", "surname": "Dupont"},
        {"role": "father", "given": "Pierre", "surname": "Dupont"},
        {"role": "mother", "given": "Marie", "surname": None},
    ],
}


def system_prompt(output_mode: str) -> str:
    return _SIMPLE_SYSTEM if output_mode == "simple" else _FULL_SYSTEM


def few_shot(output_mode: str) -> list[dict[str, str]]:
    """Few-shot turns as chat messages (fictional act, no real person)."""
    if output_mode == "simple":
        example = ActSummary.model_validate(_SIMPLE_EXAMPLE)
        payload = example.model_dump_json()
    else:
        example = Act.model_validate(_FULL_EXAMPLE)
        payload = example.model_dump_json(exclude_none=True)
    return [
        {"role": "user", "content": "[image of a 1703 baptism record]"},
        {"role": "assistant", "content": payload},
    ]


def user_prompt(act_type_hint: str | None = None, output_mode: str = "full") -> str:
    hint = (
        f"\nThe caller believes this is a {act_type_hint} act; verify against the image."
        if act_type_hint
        else ""
    )
    if output_mode == "simple":
        return "Transcribe the act in this image as the concise JSON described above." + hint
    schema = json.dumps(Act.model_json_schema(), ensure_ascii=False)
    return (
        "Transcribe the act in this image into the JSON schema below.\n\n"
        f"JSON schema:\n{schema}{hint}"
    )
