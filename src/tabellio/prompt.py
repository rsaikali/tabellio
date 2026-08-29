"""The extraction prompt and few-shot examples, versioned.

Bump ``PROMPT_VERSION`` whenever the wording changes so extractions stay
traceable to the instructions that produced them.
"""

from __future__ import annotations

import json

from tabellio.schema import Act

PROMPT_VERSION = "1"

SYSTEM_PROMPT = """\
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


def few_shot() -> list[dict[str, str]]:
    """Return few-shot turns as chat messages (fictional act, no real person)."""
    example = Act.model_validate(
        {
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
    )
    return [
        {"role": "user", "content": "[image of a 1703 baptism record]"},
        {"role": "assistant", "content": example.model_dump_json(exclude_none=True)},
    ]


def user_prompt(act_type_hint: str | None = None) -> str:
    hint = (
        f"\nThe caller believes this is a {act_type_hint} act; verify against the image."
        if act_type_hint
        else ""
    )
    return (
        "Transcribe the act in this image into the JSON schema below.\n\n"
        f"JSON schema:\n{json.dumps(Act.model_json_schema(), ensure_ascii=False)}"
        f"{hint}"
    )
