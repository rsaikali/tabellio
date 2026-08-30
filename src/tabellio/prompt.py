"""The extraction prompts and few-shot examples.

Three output modes, each with its own system prompt, few-shot and target schema:

- ``full``          -> :class:`tabellio.schema.Act` (raw spelling, confidence, notes).
- ``simple``        -> :class:`tabellio.schema.ActSummary` (identity fields only).
- ``transcription`` -> :class:`tabellio.schema.Transcription` (verbatim text only).
"""

from __future__ import annotations

import json

from tabellio.schema import Act, ActSummary, Transcription

_FULL_SYSTEM = """\
You are a palaeographer transcribing a single archival vital record (civil
registry, parish register, notarial act or similar) from an image. The act may
be in any language or script -- French, Latin, German, Dutch, Spanish, Italian,
English, and so on. Produce a strict JSON object matching the provided schema.

Rules:
- Transcribe, do not translate. Every free-text value stays in the language and
  spelling of the act. Latinised names stay Latinised ("Joannes", not "Jean");
  place names stay as written.
- Keep the exact original spelling in every `raw` field: archaic forms,
  diacritics, ligatures, scribal abbreviations.
- You may expand a clear abbreviation in `value` (e.g. "Jo~es" -> "Joannes") but
  never beyond what the abbreviation stands for.
- Split a nobiliary/toponymic particle ("de", "van", "von", "du") into
  `name_particle` and a generational suffix ("fils", "junior", "II") into
  `name_suffix`; the core family name goes in `surname`.
- Never invent a name, date, place or fact that is not legible in the image.
- `transcription`: the COMPLETE text of the act, word for word, in its own
  language, keeping the original spelling and the line breaks. Do not paraphrase
  or summarise. Write "[?]" for a single word you cannot read and "[illegible]"
  for a longer unreadable passage. This is the diplomatic transcription; the
  structured fields are extracted from it.
- For each transcribed field give a `confidence` between 0 and 1.
- Keep the act's own date (`date`: the baptism / burial / marriage ceremony or
  the registration) separate from the life events it records. For a baptism,
  fill the child's real birth in `persons[subject].birth_date` / `birth_place`
  whenever the act states it or lets you deduce it ("ne la veille", "born this
  morning", "hier", "aujourd'hui a six heures"). For a death or burial, do the
  same with `persons[subject].death_date` / `death_place`. These are often on a
  different day from the act itself.
- Every date has a `qualifier`: "exact" (given in full), "about", "before",
  "after", "between" (put both bounds in `note`), or "calculated" (deduced from
  an age or from "la veille" / "hier" ...). Any value other than "exact" needs a
  `note`.
- `calendar`: "gregorian" (default), "julian", or "french_republican" (French
  acts of an II-XIV, 1793-1805). For a non-Gregorian date keep the wording in
  `raw` and still give the proleptic-Gregorian equivalent in `iso` when you can.
- If a field cannot be read, leave it null and add a short `note`. Do not guess.
- `language`: the act's main language as an ISO 639-1 code ("fr", "la", "de"...).
- `source_hint`: "parish" for religious registers, "civil" for state civil
  registration, "unknown" if you cannot tell.
- `type` and every `role` use the schema's English vocabulary regardless of the
  language of the act.
- Output JSON only. No prose, no markdown fences.
"""

_SIMPLE_SYSTEM = """\
You are a palaeographer transcribing a single archival vital record from an
image, in any language or script. Return a strict JSON object with EXACTLY these
keys:

- "type": one of birth, baptism, marriage, death, burial
- "date": the date of the act as ISO "YYYY-MM-DD" (or "YYYY-MM" / "YYYY" if only
  that is legible), else null
- "location": the town or parish, as written, else null
- "persons": array of objects {"role", "given", "surname"} where role is one of
  subject, father, mother, groom, bride, witness, godparent, officiant,
  declarant, spouse, other

Transcribe, do not translate: names and places stay in the language and spelling
of the act (Latinised names stay Latinised). Use null for anything you cannot
read. Do not guess, do not explain. No extra keys. Output JSON only, no markdown
fences.
"""

_TRANSCRIPTION_SYSTEM = """\
You are a palaeographer transcribing a single archival vital record from an
image, in any language or script. Return a strict JSON object with EXACTLY two
keys:

- "text": the COMPLETE text of the act, word for word, in its own language, with
  the original spelling and line breaks kept. Never paraphrase or summarise.
  Write "[?]" for a single word you cannot read and "[illegible]" for a longer
  unreadable passage.
- "language": the act's main language as an ISO 639-1 code ("fr", "la", "de"...).

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
    "transcription": (
        "Le douziesme jour de may mil sept cens trois a este baptisee Jeanne\n"
        "fille de Pierre Dupont laboureur et de Marie [?] sa femme nee la\n"
        "veille. Parrain [illegible] marraine Anne Dupont."
    ),
    "persons": [
        {
            "role": "subject",
            "given": {"value": "Jeanne", "raw": "Jeanne", "confidence": 0.95},
            "surname": {"value": "Dupont", "raw": "Dupont", "confidence": 0.8},
            "birth_date": {
                "raw": "nee la veille",
                "iso": "1703-05-11",
                "qualifier": "calculated",
                "confidence": 0.8,
                "note": "act says 'nee la veille'; act dated 1703-05-12",
            },
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
    "language": "fr",
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

_TRANSCRIPTION_EXAMPLE = {
    "text": (
        "Le douziesme jour de may mil sept cens trois a este baptisee Jeanne\n"
        "fille de Pierre Dupont laboureur et de Marie [?] sa femme nee la\n"
        "veille. Parrain [illegible] marraine Anne Dupont."
    ),
    "language": "fr",
}


_SYSTEM = {
    "full": _FULL_SYSTEM,
    "simple": _SIMPLE_SYSTEM,
    "transcription": _TRANSCRIPTION_SYSTEM,
}


def system_prompt(output_mode: str) -> str:
    return _SYSTEM[output_mode]


def few_shot(output_mode: str) -> list[dict[str, str]]:
    """Few-shot turns as chat messages (fictional act, no real person)."""
    if output_mode == "transcription":
        payload = Transcription.model_validate(_TRANSCRIPTION_EXAMPLE).model_dump_json()
    elif output_mode == "simple":
        payload = ActSummary.model_validate(_SIMPLE_EXAMPLE).model_dump_json()
    else:
        payload = Act.model_validate(_FULL_EXAMPLE).model_dump_json(exclude_none=True)
    return [
        {"role": "user", "content": "[image of a 1703 baptism record]"},
        {"role": "assistant", "content": payload},
    ]


def user_prompt(
    act_type_hint: str | None = None,
    output_mode: str = "full",
    act_language_hint: str | None = None,
    context: str | None = None,
) -> str:
    hints = ""
    if act_type_hint:
        hints += f"\nThe caller believes this is a {act_type_hint} act; verify against the image."
    if act_language_hint:
        hints += (
            f"\nThe caller believes the act is written in {act_language_hint}; "
            "verify against the image."
        )
    if context:
        hints += (
            "\n\nThe caller already knows the following about this act. Use it only to "
            "resolve genuinely ambiguous or hard-to-read passages -- never to override a "
            "clear reading on the image. Where the context conflicts with what is plainly "
            "written, follow the image"
            + (
                " and add a `note` on the affected field explaining the discrepancy.\n"
                if output_mode == "full"
                else ".\n"
            )
            + f"Caller context: {context.strip()}"
        )
    if output_mode == "transcription":
        return "Transcribe the complete text of the act in this image, as the JSON above." + hints
    if output_mode == "simple":
        return "Transcribe the act in this image as the concise JSON described above." + hints
    schema = json.dumps(Act.model_json_schema(), ensure_ascii=False)
    return (
        "Transcribe the act in this image into the JSON schema below.\n\n"
        f"JSON schema:\n{schema}{hints}"
    )
