# examples/

Sample acts and their extracted output, for the README and for eyeballing
changes.

## Hard rule: no real personal data

This repository is public. Only put here:

- **fictional acts** written for the purpose, or
- **public-domain historical records**: registers older than 120 years, no
  identifiable living person.

Never a user-supplied scan, never a family act. See the project `CLAUDE.md`.

## Contents

| File | What |
|---|---|
| `sample_act.jpg` | A 1757 parish burial act (Joseph Bommal — the initial reads ambiguously B/C). Public-domain, >120 years. |
| `sample_act.full.json` | `parse(..., output_mode="full")` |
| `sample_act.simple.json` | `parse(..., output_mode="simple")` |
| `sample_act.transcription.json` | `parse(..., output_mode="transcription")` |
| `sample_act.gedcom` | `to_gedcom(parse(...))` — GEDCOM 7.0 |

Reference output produced with `gemini`. Not asserted by the test suite —
regenerate and eyeball them when the schema or the prompts change.
