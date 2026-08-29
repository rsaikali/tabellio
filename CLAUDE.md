# tabellio

Python library: image of a civil-registry / parish record → validated
structured JSON.

> *tabellio*: the Roman / medieval scribe who officially drafted legal acts.

## Language: English only

**This entire project is English — no French anywhere.** Code, comments,
docstrings, logs, tests, README, docs, commit messages, and **this
`CLAUDE.md`**. It is a public library. Talk to the user in its preferred language, write
every persisted artifact in English.

## Public repo — no real data

This repo is public and stays public. Therefore: **no real personal data** in
the repo, ever. Examples, fixtures and tests use fictional acts or public-domain
historical records (registers > 120 years old, no identifiable living person).
Never a user-supplied scan, never a family act. (Re-added after an edit dropped
it — it matters here because the sibling project it came from exists precisely
to keep that kind of data private.)

## Rationale — why this shape

Decision chain, in the order it was settled:

1. **No local vision model.** On old cursive, local and
   general-purpose VLMs hallucinate plausible names/dates — poison for
   genealogy. Reliability comes from validation and schema, not the model.
2. **No home-grown trained HTR.** Transkribus / kraken have mature models a solo
   dev won't beat. The differentiator is elsewhere: clean act schema, ambiguity
   rules, confidence surfacing, exports.
3. **Not a SaaS.** Billing, quotas, support, model hosting, and above all
   **GDPR**: hosting third-party uploads of recent people's acts means becoming
   a data processor. That is a company, not a portfolio project.
4. **BYOK (bring your own key).** The caller supplies their own API key as a
   call parameter. Ideally key + image go straight from the client to the
   provider, so this library's code sees neither — no processing liability.
5. **So: a library**, plus (later) a static BYOK demo page as a showcase
   artifact.
6. **Provider-agnostic.** NIM is one backend among several.
   Gemini Flash reads acts better in practice; many people already have
   a Gemini/OpenAI/Anthropic key and no NIM key.

## Decisions

| Topic | Decision |
|---|---|
| Form | Published Python library (PyPI: `tabellio`) |
| License | Permissive open source (MIT or Apache-2.0) |
| Language | **English everywhere** (see top). User-facing conversation stays in his preferred language. |
| Model | No embedded / trained model. Calls a third-party VLM via a backend. |
| API key | **BYOK** — supplied by the caller, never stored, never logged. |
| Backends | Thin multi-provider adapter: NIM, Gemini, OpenAI, Anthropic, Ollama (optional local). None required at install. |
| Output | JSON validated by a **Pydantic** schema. |
| Ambiguity | No silent resolution: keep the original spelling, flag inferred dates, `confidence`. |
| Storage | **None.** No database, no disk cache of user content. |
| Accounts / billing | **None.** Permanently out of scope for the library. |

## Output schema (target)

An extracted act yields at least:

- `type`: `birth` | `baptism` | `marriage` | `death` | `burial`
- `date`: date of the act + raw spelling (`raw`), `confidence`
- `place`: town / parish
- `persons[]`: role (subject, father, mother, groom, bride, witness, godparent…),
  `given` / `surname`, dates and places cited, per-field `confidence`
- `other[]`: occupations (`occupation`), marginal notes, reading notes
- `source_hint`: guessed register type (parish vs civil registry) from the date
- unread fields → absent or `null` + note, **never guessed**

The exact schema lives in code (`tabellio/schema.py` or similar), not here —
this table is intent only.

## Target architecture

```
tabellio.parse(image, backend="gemini"|"nim"|"openai"|"anthropic"|"ollama",
               api_key=..., act_type_hint=None) -> Act   # Pydantic
```

- `src/tabellio/backends/`: one module per provider, common interface
  `(image, prompt, schema) -> raw_json`. Lazy import of optional SDKs.
- `src/tabellio/schema.py`: Pydantic models (`Act`, `Person`, `GenDate`…).
- `src/tabellio/validate.py`: post-extraction rules (date/role consistency, 2-digit years,
  `confidence`).
- `src/tabellio/prompt.py`: the extraction prompt + few-shot, versioned.
- No mandatory CLI at first; a simple `python -m tabellio <image>` can come
  later.

## Out of scope — refuse

- Embedded local model, fine-tuning, home-grown HTR.
- Storage, accounts, billing, dashboard, job queue.
- GEDCOM re-import or writing into a tree — the library **extracts**, full stop.
- Image segmentation / heavy pre-processing (deskew, binarization) in v1.
- Languages beyond French while no non-FR act is tested.

## Stack

Python 3.14, `uv` (deps/venv), `ruff` (lint + format), `pytest`. `loguru` for
logs. Pydantic v2. Provider SDKs as optional dependencies
(`pip install tabellio[gemini]` etc.).
