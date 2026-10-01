# Contributing

Thanks for helping. By taking part you agree to the ThetaPlex
[Code of Conduct](https://github.com/thetaplex/.github/blob/main/CODE_OF_CONDUCT.md).
Report security issues privately, as described in [SECURITY.md](SECURITY.md).

Thetaterm is maintained by the [ThetaPlex](https://github.com/thetaplex)
organization, which enforces the Code of Conduct. Reach it at
support@thetaplex.com.

## Setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[just](https://just.systems/man/en/packages.html).

```bash
git clone https://github.com/thetaplex/thetaterm
cd thetaterm
just setup
uvx pre-commit install
```

Day to day:

```bash
cp .env.example .env    # optional local settings; just loads it
just run                # interactive; just run -q "..." for one request
just check              # lint, format check, tests
just fmt                # format
```

`just` with no arguments lists every recipe. To understand the code before
changing it, read [How it works](docs/explanation/how-it-works.md) and the
[architecture decision records](docs/adr/).

## Making a change

1. Branch from `main`. The pre-commit hook blocks commits to `main`.
2. Add or update a test in `tests/` for any change in behaviour.
3. Run `just check`. CI runs the same recipe on Linux and macOS.
4. If the change affects what the model is asked or how its reply is read, run
   `just eval` against at least one local model. See
   [How to run the evals](docs/how-to/run-evals.md).
5. Add a line under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
6. If the change affects behaviour users see, update the pages in `docs/`.
7. If it reverses or replaces a recorded decision, add a new ADR in `docs/adr/`
   that supersedes the old one. Don't edit accepted ADRs.
8. Open a pull request saying what changed and why.

Bugs and ideas go in [issues](https://github.com/thetaplex/thetaterm/issues).
For a wrong command, include the query, the model, and your OS and shell.
