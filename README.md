# tabellio

Turn an image of a civil-registry or parish record into **validated structured
JSON**.

> *tabellio*: the Roman / medieval scribe who officially drafted legal acts.

- **BYOK** — you pass your own VLM API key; it is never stored, never logged.
- **Provider-agnostic** — Gemini, OpenAI, NVIDIA NIM, Anthropic, or a local
  Ollama model. None required at install.
- **No embedded model, no training, no storage.** Reliability comes from a
  strict [Pydantic](https://docs.pydantic.dev) schema and post-extraction
  consistency rules, not from trusting the model.
- **No silent resolution.** Original spelling is kept, inferred dates are
  flagged, every field carries a `confidence`.

## Install

```bash
pip install "tabellio[gemini]"     # or [openai] / [nim] / [anthropic] / [ollama] / [all]
```

Requires Python 3.11+.

## Use

```python
import tabellio

act = tabellio.parse(
    "register-page.jpg",
    provider="gemini",
    api_key="...",  # your key, BYOK
    act_type_hint="baptism",  # optional
)

print(act.type)  # ActType.BAPTISM
print(act.date.raw)  # "le douziesme jour de may mil sept cens trois"
print(act.date.iso)  # "1703-05-12"
for p in act.persons:
    print(p.role, p.given.value if p.given else None, p.surname.raw if p.surname else None)
print(act.warnings)  # consistency + low-confidence flags
```

`parse()` returns an [`Act`](src/tabellio/schema.py) Pydantic model. Unread
fields are `null` with a note — never guessed.

### Output modes

```python
act = tabellio.parse("register-page.jpg", output_mode="simple")
# ActSummary: type, date, location, persons[{role, given, surname}] — nothing else
```

- `output_mode="full"` (default) — rich `Act`: raw spelling, per-field
  `confidence`, inference flags, validation `warnings`.
- `output_mode="simple"` — sends a shorter prompt, returns a bare `ActSummary`:
  `type`, `date` (ISO string or `null`), `location`, `persons`. No confidence,
  no raw, no inference, no notes. Fewer tokens in and out.

### Configuration

Three optional environment variables, each a fallback for the matching
`parse()` argument. An explicit argument always wins.

| Variable | Fills | Default |
|---|---|---|
| `TABELLIO_PROVIDER` | `provider=` | `gemini` |
| `TABELLIO_KEY` | `api_key=` | — (required except `ollama`) |
| `TABELLIO_MODEL` | `model=` | the provider's default |

The key is never logged and never stored.

### Command line

```bash
export TABELLIO_PROVIDER=gemini
export TABELLIO_KEY=...              # in your shell
python -m tabellio data/act.jpg [--hint baptism] [--output simple] [-v]
```

Prints the act as JSON on stdout, warnings on stderr. The key is only read
from the environment — never a CLI argument. `--provider`, `--model` and
`--output` override the defaults.

## Providers

| `provider=` | Extra | Default model |
|---|---|---|
| `gemini` | `tabellio[gemini]` | `gemini-3.6-flash` |
| `openai` | `tabellio[openai]` | `gpt-4o` |
| `nim` | `tabellio[nim]` | `meta/llama-3.2-90b-vision-instruct` |
| `anthropic` | `tabellio[anthropic]` | `claude-sonnet-4` |
| `ollama` | `tabellio[ollama]` | `llama3.2-vision` (local, no key) |

Set `TABELLIO_MODEL` (or pass `model=`) to switch model — quality vs speed is
your call. Provider-specific keyword options pass straight through
(`base_url=`, `host=`, `max_tokens=`, ...).

> Local / general-purpose VLMs hallucinate plausible names and dates on old
> cursive. The `ollama` provider exists for convenience and testing, not for
> production genealogy.

## Scope

**In:** extraction of a single record to schema, ambiguity flags, confidence
surfacing, provider-agnostic adapter.

**Out:** embedded/trained model, home-grown HTR, storage, accounts, billing,
GEDCOM import or writing into a tree, image segmentation / deskew, languages
beyond French (until a non-FR act is tested).

## Development

```bash
make install     # uv sync --all-extras
make lint        # ruff check + format --check
make test        # pytest
```

The `data/` directory holds example acts — **fictional or public-domain only**,
see [`data/README.md`](data/README.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
