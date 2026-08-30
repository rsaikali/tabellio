# tabellio

Turn an image of a civil-registry or parish record into **validated structured
JSON**.

> *tabellio*: the Roman / medieval scribe who officially drafted legal acts —
> the *vieux tabellion* Georges Brassens addresses in *Supplique pour être
> enterré sur la plage de Sète* (1966):
>
> > *Trempe dans l'encre bleue du Golfe du Lion,*
> > *Trempe, trempe ta plume, ô mon vieux tabellion,*
> > *Et de ta plus belle écriture,*
> > *Note ce qu'il faudrait qu'il advînt de mon corps…*
>
> This library reads back what that pen wrote.

- **BYOK** — you pass your own VLM API key; it is never stored, never logged.
- **Provider-agnostic** — Gemini, OpenAI, NVIDIA NIM, Anthropic, or a local
  Ollama model. None required at install.
- **No embedded model, no training, no storage.** Reliability comes from a
  strict [Pydantic](https://docs.pydantic.dev) schema and post-extraction
  consistency rules, not from trusting the model.
- **No silent resolution.** Original spelling is kept, every date carries a
  `qualifier` (exact / about / calculated / …), every field a `confidence`.
- **Verbatim transcription too.** The full diplomatic text of the act, `[?]` for
  an illegible word — as `act.transcription` in full mode, or on its own with
  `output_mode="transcription"`.
- **GEDCOM 7 out of the box.** `tabellio.to_gedcom(act)` — schema built to map
  cleanly to GEDCOM.
- **Any language or script.** Text is transcribed in the language of the act
  (Latin, French, German, …) and **never translated**; only the schema's
  `type` / `role` vocabulary is fixed English. The detected language is recorded
  on `act.language`.

## Example

A parish burial act from 1757, a public-domain register page,
[`examples/sample_act.jpg`](examples/sample_act.jpg):

![1757 burial act](examples/sample_act.jpg)

```bash
export TABELLIO_KEY=...
for mode in full simple transcription; do
    python -m tabellio examples/sample_act.jpg --hint burial --output "$mode"
done
```

| Mode | Output | What you get |
|---|---|---|
| `full` | [`sample_act.full.json`](examples/sample_act.full.json) | every field, `raw` spelling, `confidence`, date `qualifier`, `transcription`, `warnings` |
| `simple` | [`sample_act.simple.json`](examples/sample_act.simple.json) | `type` / `date` / `location` / `persons` only |
| `transcription` | [`sample_act.transcription.json`](examples/sample_act.transcription.json) | the verbatim text + detected language |

*(The `.json` files land once the reference run against `gemini` is done.)*

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
for mode in ("full", "simple", "transcription"):
    print(tabellio.parse("register-page.jpg", output_mode=mode))
```

- `output_mode="full"` (default) — rich `Act`: raw spelling, per-field
  `confidence`, date `qualifier`, `transcription`, validation `warnings`.
  `act.date` is the date of the *act*; the subject's real **birth / death**
  (often a different day — *"né la veille"*, *"décédé hier"*) lands on
  `persons[i].birth_date` / `death_date` with `qualifier: "calculated"` + a note
  when deduced. `validate` warns if a baptism or burial has no such date on its
  subject.
- `output_mode="simple"` — a bare `ActSummary`: `type`, `date` (ISO string or
  `null`), `location`, `persons` (role / given / surname). Nothing else — no
  confidence, no raw, no qualifiers, no `language`, no life-event dates, no
  transcription. Shortest prompt, fewest tokens.
- `output_mode="transcription"` — just `Transcription`: the verbatim `text` of
  the act (`[?]` / `[illegible]` for gaps) plus the detected `language`.

### Hints

```python
tabellio.parse(
    img,
    act_type_hint="burial",  # --hint
    act_language_hint="fr",  # --lang
    context="The deceased is Joseph BOMMAL, buried 21 December 1757.",  # --context
)
```

All three are optional. `act_type_hint` / `act_language_hint` are guesses the
model verifies against the image. `context` is free text of whatever you already
know — names, a date, a place. It is used **only** to disambiguate hard-to-read
passages: it never overrides a clear reading, `raw` stays faithful to the page,
and in `full` mode the model adds a `note` wherever it followed the image
against your context.

### GEDCOM

```python
act = tabellio.parse("register-page.jpg")  # the one network call
print(act.model_dump_json(indent=2))  # JSON
print(tabellio.to_gedcom(act))  # a complete GEDCOM 7.0 document
```

`to_gedcom(act)` writes one `SOUR` record for the act, one `INDI` per person it
names, and a `FAM` for the couple or parent-child link the act *states* —
`BIRT` / `BAPM` / `MARR` / `DEAT` / `BURI` events with `DATE` / `PLAC` / `AGE`,
`ASSO` + `ROLE` for witnesses and godparents, `QUAY` from `confidence`. It
transcribes one act; it does **not** merge a tree — your genealogy software does
that on import. Output is conformance-checked against the `gedcom7` library in
the test suite.

CLI: `python -m tabellio examples/sample_act.jpg --format gedcom`.

The schema is GEDCOM-mappable by design: `GenDate.qualifier`
(`about`/`before`/`after`/`calculated` → `ABT`/`BEF`/`AFT`/`CAL`),
`GenDate.calendar` (`julian`, `french_republican`), `Person.name_particle`
(`SPFX`), `Person.name_suffix` (`NSFX`).

### Configuration

Three optional environment variables, each a fallback for the matching
`parse()` argument. An explicit argument always wins. tabellio reads them from
`os.environ` — it does not load a `.env` file; your application manages its own
environment.

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
python -m tabellio examples/sample_act.jpg [--hint baptism] [--lang fr] [--context "..."] \
    [--output simple|transcription] [--format gedcom] [-v]
```

Prints the act as JSON (or GEDCOM 7 with `--format gedcom`, or plain text with
`--output transcription`) on stdout, warnings on stderr. The key is only read
from the environment — never a CLI argument.

## Providers

| `provider=` | Extra | Default model |
|---|---|---|
| `gemini` | `tabellio[gemini]` | `gemini-3.6-flash` |
| `openai` | `tabellio[openai]` | `gpt-4o` |
| `nim` | `tabellio[nim]` (pulls Pillow) | `meta/llama-3.2-11b-vision-instruct` |
| `anthropic` | `tabellio[anthropic]` | `claude-sonnet-4` |
| `ollama` | `tabellio[ollama]` | `llama3.2-vision` (local, no key) |

Set `TABELLIO_MODEL` (or pass `model=`) to switch model — quality vs speed is
your call. Keyword options pass straight through: `timeout=` (seconds, default
120), `base_url=`, `host=`, `max_tokens=`.

**NIM caveat.** On the hosted free endpoint (`integrate.api.nvidia.com`) the 90B
vision model routinely times out; the default is therefore
`meta/llama-3.2-11b-vision-instruct`, which answers in seconds but is a small
model — it hallucinates names and dates on old cursive and returns poor results
here. Use `--output simple` with it, and treat `gemini` as the real path.
The endpoint also rejects inline images larger than ~180 KB: tabellio re-encodes
an oversized image **in memory** (lower JPEG quality, then downscale, long edge
kept ≥ 1200 px) before sending — the source file is never touched — and logs a
warning; pass `shrink=False` to get an error instead. NVCF asset upload is not
implemented.

> Local / general-purpose VLMs hallucinate plausible names and dates on old
> cursive. The `ollama` provider exists for convenience and testing, not for
> production genealogy.

## Scope

**In:** extraction of a single record to schema, ambiguity flags, confidence
surfacing, provider-agnostic adapter, JSON and GEDCOM 7 output.

**Out:** embedded/trained model, home-grown HTR, storage, accounts, billing,
GEDCOM *import*, building or merging a family tree, image segmentation / deskew,
**translation** of any transcribed text.

## Development

```bash
make install     # uv sync --all-extras
make lint        # ruff check + format --check
make test        # pytest
```

To run `python -m tabellio` against a real provider while developing, export
`TABELLIO_KEY` (and optionally `TABELLIO_PROVIDER` / `TABELLIO_MODEL`) in your
shell, or use your own `direnv` / dotenv — the repo ships none.

The `examples/` directory holds a sample act and its extracted output —
**fictional or public-domain only**, see [`examples/README.md`](examples/README.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
