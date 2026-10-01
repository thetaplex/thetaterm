# Security Policy

## Supported versions

Only the latest release on `main` gets security fixes.

## Reporting a vulnerability

Report privately, not in a public issue:

- [Open a private advisory](https://github.com/thetaplex/thetaterm/security/advisories/new), or
- email support@thetaplex.com.

Include what you ran, what happened, and the model and endpoint if relevant.
You'll get a reply within 7 days.

## Scope

Thetaterm runs shell commands a model writes. In scope:

- a command running without confirmation when it should have asked
- the outside-the-current-directory check missing a plain path, `~`, `..`,
  a variable, a bare `cd`, `cd -`, `popd`, or `sudo`
- Thetaterm running any program before you confirm a command
- the API key reaching an endpoint other than `THETATERM_BASE_URL`, or config
  being read from somewhere other than the per-user `.env`

Out of scope: harmful commands you approved, anything run with `-y`, and
commands built on purpose to hide what they touch. The README says the
outside-directory check is a pattern match, not a sandbox.
