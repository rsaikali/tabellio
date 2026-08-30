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
| `sample_act.jpg` | A 1757 burial act (Joseph Bommal). Public-domain, >120 years. |
| `sample_act.full.json` | `tabellio.parse(..., output_mode="full")` output *(to be added)* |
| `sample_act.simple.json` | `output_mode="simple"` output *(to be added)* |
| `sample_act.transcription.json` | `output_mode="transcription"` output *(to be added)* |

The `.json` files are committed reference output produced with `gemini` — regenerate
and review them by hand when the schema or the prompts change, they are not
asserted by the test suite.
