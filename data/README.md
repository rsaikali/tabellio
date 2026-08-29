# data/

Example acts for manual testing and documentation.

## Hard rule: no real personal data

This repository is public. Only put here:

- **Fictional acts** you wrote yourself, or
- **Public-domain historical records**: registers older than 120 years, with no
  identifiable living person.

Never a user-supplied scan. Never a family act. Never anything received from
someone else. See the project `CLAUDE.md` ("Public repo — no real data").

## Layout

```
data/
  <name>.jpg|png|tiff        # the image of a single record
  <name>.expected.json       # optional: the Act JSON you expect back
```

Drop files in and they will be picked up by the example scripts / integration
tests. `.expected.json` files, when present, are compared field by field.
