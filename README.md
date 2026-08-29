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
    backend="gemini",
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

## Backends

| `backend=` | Extra | Default model | Key parameter |
|---|---|---|---|
| `gemini` | `tabellio[gemini]` | `gemini-2.0-flash` | `api_key` |
| `openai` | `tabellio[openai]` | `gpt-4o` | `api_key` |
| `nim` | `tabellio[nim]` | `llama-3.2-90b-vision-instruct` | `api_key` |
| `anthropic` | `tabellio[anthropic]` | `claude-sonnet-4` | `api_key` |
| `ollama` | `tabellio[ollama]` | `llama3.2-vision` | — (local) |

Override with `model=` or backend-specific keyword options (`base_url=`,
`host=`, ...).

> Local / general-purpose VLMs hallucinate plausible names and dates on old
> cursive. The `ollama` backend exists for convenience and testing, not for
> production genealogy.

## Scope

**In:** extraction of a single record to schema, ambiguity flags, confidence
surfacing, multi-provider adapter.

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
