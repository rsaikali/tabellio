# Security policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately via GitHub's
["Report a vulnerability"](https://github.com/rsaikali/tabellio/security/advisories/new)
button, or by opening a minimal issue asking for a private channel. Do not file a
public issue with exploit details.

You can expect an acknowledgement within a few days. This is a solo,
best-effort project.

## Scope notes

- tabellio is **BYOK**: the caller passes their own VLM API key as a parameter.
  The library never stores or logs it. It is sent only to the provider the
  caller selected.
- No network listener, no persistence, no telemetry.
- The one non-obvious network path: `tabellio.parse` sends the supplied image
  and prompt to the chosen provider's HTTPS API.
