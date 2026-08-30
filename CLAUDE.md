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
6. **Provider-agnostic.** NIM is one provider among several.
   Gemini Flash reads acts better in practice; many people already have
   a Gemini/OpenAI/Anthropic key and no NIM key.

## Decisions

| Topic | Decision |
|---|---|
| Form | Published Python library (PyPI: `tabellio`) |
| License | Permissive open source (MIT or Apache-2.0) |
| Language | **English everywhere** (see top). User-facing conversation stays in his preferred language. |
| Model | No embedded / trained model. Calls a third-party VLM via a provider adapter. |
| API key | **BYOK** — supplied by the caller, never stored, never logged. |
| Config | Three env vars, each a fallback for a `parse()` arg (explicit arg wins): `TABELLIO_PROVIDER`, `TABELLIO_KEY`, `TABELLIO_MODEL`. Nothing else read from the environment. |
| Providers | Thin multi-provider adapter: Gemini, Mistral, OpenAI, Anthropic, NIM, Ollama (optional local). None required at install. Free tiers (no cost): **Gemini** (best on acts) and **Mistral** (`mistral-small-latest` default, `pixtral-*` deprecated → vision folded into Small/Medium). `mistral` uses the `mistralai` 2.x SDK (`from mistralai.client import Mistral`). All take `timeout=` (default 120s), `max_retries=0`. **NIM hosted endpoint rejects inline images >180 KB** (NVCF asset upload not implemented) → `NIMProvider` re-encodes in memory via `image.fit_within` (JPEG quality down, then downscale, long edge ≥ 1200 px; source untouched; loguru warning), or raises with `shrink=False`. Needs Pillow (`tabellio[nim]` / `tabellio[resize]`). Default model `meta/llama-3.2-11b-vision-instruct` (the 90B times out on the free tier) — small, hallucinates on cursive, use `output_mode="simple"`. **Gemini is the real path; NIM is runnable, not good.** |
| Output | JSON validated by a **Pydantic** schema. Three `output_mode`s, each its own prompt + target model: `"full"` (default) -> `Act`; `"simple"` -> `ActSummary` (type/date/location/persons, nothing else); `"transcription"` -> `Transcription` (verbatim `text` + `language`). |
| Transcription | Complete verbatim diplomatic transcription, source language + line breaks kept, `[?]` = one illegible word, `[illegible]` = a longer passage. As `Act.transcription` in full mode (`validate` warns if missing; GEDCOM `SOUR.TEXT`) or as the whole result in `"transcription"` mode. **Not** in `simple`. |
| Serialisers | One `parse()` (the only network call). `act.model_dump_json()` = JSON. `tabellio.to_gedcom(act)` = a complete **GEDCOM 7.0** document (`gedcom.py`; conformance-checked in tests against the `gedcom7` lib). No YAML helper (one-liner + a dep). Schema is GEDCOM-mappable by design: `GenDate.qualifier`/`calendar`, `Person.name_particle`/`name_suffix`, `Role` → `ASSO.ROLE`. |
| Ambiguity | No silent resolution: keep the original spelling, `qualifier` on every date, per-field `confidence`. |
| Hints | `act_type_hint` (`--hint`, enum) and `act_language_hint` (`--lang`, ISO code) — guesses verified against the image. `context` (`--context`, free text: names / date / place the caller already knows) — used **only** to disambiguate hard-to-read passages, never to override a clear reading; `raw` stays faithful; full mode adds a `note` where image beats context. |
| Act language | **International.** Any language or script (French, Latin, German, Dutch, Spanish, …). **Transcribe, never translate**: `raw`/`value` free text stays in the source language, Latinised names stay Latinised. Only `type` and `role` are a fixed English vocabulary. `Act.language` = model-detected ISO 639-1 code (full mode only). Optional `act_language_hint=` / `--lang`, verified against the image like `act_type_hint`. |
| Storage | **None.** No database, no disk cache of user content. |
| Accounts / billing | **None.** Permanently out of scope for the library. |

## Output schema (target)

An extracted act yields at least:

- `type`: `birth` | `baptism` | `marriage` | `death` | `burial`
- `date`: date **of the act** (the ceremony / registration) + raw spelling (`raw`), `confidence`
- `place`: town / parish
- `transcription`: complete verbatim text of the act, `[?]` / `[illegible]` for gaps
- `persons[]`: role (subject, father, mother, groom, bride, witness, godparent…),
  `given` / `surname` / `name_particle` (SPFX) / `name_suffix` (NSFX), per-field
  `confidence`, plus the **life-event** dates and places on the person:
  `birth_date` / `birth_place`, `death_date` / `death_place`. For a baptism the
  subject's real birth (often "né la veille" etc.) goes in `birth_date`; for a
  burial the death goes in `death_date`. `validate` flags a baptism/burial whose
  subject has no such date.
- `GenDate`: `raw`, `iso` (always proleptic-Gregorian), `qualifier`
  (`exact|about|before|after|between|calculated` → GEDCOM `ABT`/`BEF`/`AFT`/`CAL`),
  `calendar` (`gregorian|julian|french_republican`), `confidence`, `note`.
- `other[]`: occupations (`occupation`), marginal notes, reading notes
- `source_hint`: guessed register type (parish vs civil registry) from the form of the act
- `language`: model-detected ISO 639-1 code (full mode only)
- unread fields → absent or `null` + note, **never guessed**

`output_mode="simple"` yields only `type`, `date` (ISO string or `null`),
`location`, `persons[{role, given, surname}]` — no raw, confidence, qualifiers,
transcription, warnings. `output_mode="transcription"` yields only
`{text, language}`. Each mode has its own `_*_SYSTEM` prompt + target model, not
a projection of `Act`.

The exact schema lives in code (`tabellio/schema.py` or similar), not here —
this table is intent only.

## Target architecture

```
tabellio.parse(image, provider="gemini"|"mistral"|"openai"|"anthropic"|"nim"|"ollama",
               api_key=..., model=None, act_type_hint=None, act_language_hint=None,
               context=None, output_mode="full"|"simple"|"transcription")
    -> Act | ActSummary | Transcription   # Pydantic
```

`provider` / `api_key` / `model` fall back to `TABELLIO_PROVIDER` /
`TABELLIO_KEY` / `TABELLIO_MODEL` when not passed.

- `src/tabellio/providers/`: one module per provider, `registry.py` holds the
  `Provider` protocol + lazy-import registry. Common interface
  `(image, prompt, ...) -> raw_json`. Lazy import of optional SDKs.
- `src/tabellio/schema.py`: Pydantic models (`Act`, `Person`, `GenDate`…).
- `src/tabellio/validate.py`: post-extraction rules (date/role consistency, 2-digit years,
  `confidence`).
- `src/tabellio/prompt.py`: the extraction prompts + few-shot. `system_prompt`
  / `few_shot` / `user_prompt` take `output_mode`. Not separately versioned —
  the package version + git is the record until users actually need more.
- `python -m tabellio <image>` exists (`__main__.py`): thin CLI, config from
  the env vars, `--provider` / `--model` / `--hint` / `--lang` / `--context` / `--output` /
  `-v`.

## Out of scope — refuse

- Embedded local model, fine-tuning, home-grown HTR.
- Storage, accounts, billing, dashboard, job queue.
- Building or **merging a family tree**. `to_gedcom` emits one act's people +
  events + the couple/parent links the act *states* — deduplication and tree
  merging happen in the genealogist's software on import. No GEDCOM re-import.
- Image segmentation / heavy pre-processing (deskew, binarization) in v1.
  (Exception: `image.fit_within` re-encodes in memory *only* to satisfy NIM's
  180 KB transport limit — not an enhancement step, never touches the source.)
- **Translation** of transcribed text. Names, places, terms and notes are kept
  verbatim in the act's language (see the "Act language" decision). A caller
  wanting a vernacular form does that downstream.

## Stack

Python 3.14, `uv` (deps/venv), `ruff` (lint + format), `pytest`. `loguru` for
logs. Pydantic v2. Provider SDKs as optional dependencies
(`pip install tabellio[gemini]` etc.).

CI (`.github/workflows/ci.yml`): `lint` job (ruff check + format --check on
3.13) and a `test` matrix on Python 3.11–3.14, all via `uv sync --all-extras` +
`uv run`. Public repo: `github.com/rsaikali/tabellio`.

Release (`.github/workflows/release.yml`, PyPI **Trusted Publishing** / OIDC, no
token): push tag `vX.Y.Z` (must equal `[project].version`) → rehearsal on
TestPyPI; publish a GitHub release → real PyPI. GH environments `testpypi` /
`pypi`. Ships `py.typed`. `CHANGELOG.md` (Keep a Changelog), `SECURITY.md`.
