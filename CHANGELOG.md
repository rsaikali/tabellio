# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `mistral` provider (`pip install 'tabellio[mistral]'`) — Mistral's multimodal
  models via the `mistralai` 2.x SDK. Default `mistral-small-latest`. Paid;
  `gemini` remains the free option.

## [0.1.1] - 2026-08-30

### Fixed

- `tabellio.__version__` now derives from the installed package metadata
  instead of a hard-coded string, so it can no longer drift from
  `pyproject.toml`. (0.1.0 was pushed to TestPyPI only, never to PyPI.)

## [0.1.0] - 2026-08-30

First public release (TestPyPI rehearsal only).

### Added

- `tabellio.parse(image, *, provider, api_key, model, act_type_hint,
  act_language_hint, context, output_mode, validate, **provider_options)` —
  one call, one network request.
- Providers: `gemini`, `openai`, `nim`, `anthropic`, `ollama` — thin adapters,
  lazy SDK imports, none required at install. Per-provider `timeout=`,
  `max_retries=0`.
- Three output modes: `full` (`Act`), `simple` (`ActSummary`), `transcription`
  (`Transcription`). Each has its own prompt and Pydantic target.
- BYOK end to end: `api_key` is a call parameter, resolved from `$TABELLIO_KEY`
  when omitted; never stored, never logged.
- `Act` schema: per-field `confidence`, `raw` spelling, date `qualifier`
  (`exact`/`about`/`before`/`after`/`between`/`calculated`) and `calendar`
  (`gregorian`/`julian`/`french_republican`), `name_particle` / `name_suffix`,
  life-event dates on persons, verbatim `transcription`, model-detected
  `language`.
- `tabellio.validate` — post-extraction consistency checks surfaced as
  `act.warnings` (never rewrites model output).
- `tabellio.to_gedcom(act)` — a complete, conformance-checked GEDCOM 7.0
  document (`SOUR` + `INDI` + `FAM`), transcription in `SOUR.TEXT`.
- `NIMProvider` re-encodes oversized images in memory (`image.fit_within`) to
  satisfy the ~180 KB inline limit; `shrink=False` to opt out.
- `python -m tabellio <image>` CLI with `--provider` / `--model` / `--hint` /
  `--lang` / `--context` / `--output` / `--format` / `--no-validate` / `-v`.

[Unreleased]: https://github.com/rsaikali/tabellio/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/rsaikali/tabellio/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/rsaikali/tabellio/releases/tag/v0.1.0
