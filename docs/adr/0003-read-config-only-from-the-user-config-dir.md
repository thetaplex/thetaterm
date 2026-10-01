# 3. Read settings only from the user's config directory

Date: 2026-09-29

## Status

Accepted

## Context

Thetaterm sends `THETATERM_API_KEY` to `THETATERM_BASE_URL`. Python tools
often load a `.env` file from the current directory or its parents. A user
running `tterm` inside a cloned repository would then use that repository's
`.env`, and a hostile one could set `THETATERM_BASE_URL` to its own server and
collect the key along with the user's requests.

Generic names like `MODEL` are also set by other tools' `.env` files and by
shells, and would change the model unexpectedly.

## Decision

Read settings from environment variables and from
`$XDG_CONFIG_HOME/thetaterm/.env` (default `~/.config/thetaterm/.env`) only.
Environment variables take priority. Never read a `.env` from the working
directory. Prefix every setting with `THETATERM_`.

Warn when an API key would be sent over plain `http://` to a host other than
localhost.

## Consequences

- A directory's contents can't redirect the key or change the model.
- Per-project settings need environment variables, for example via `direnv`
  or the shell.
- Developers working on Thetaterm itself use `.env` in the repository through
  `just`, which loads it explicitly.
- Renaming `MODEL` to `THETATERM_MODEL` broke existing setups. That happened
  before the first release.
