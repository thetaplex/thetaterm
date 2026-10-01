# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `tterm`: describe a task, get a shell command for your OS, tool flavour
  (GNU, BSD, BusyBox) and login shell (sh, bash, zsh, ksh, dash; others
  fall back to bash), confirm, run.
- Interactive mode, and one-shot mode with `-q`.
- Any OpenAI-compatible endpoint via `THETATERM_BASE_URL`, with
  `THETATERM_MODEL` and `THETATERM_API_KEY`.
- Settings read from `~/.config/thetaterm/.env`.
- The relevant parts of the installed command's `man` page go into the
  prompt, or its `--help` output for commands you name that have no `man` page.
- A syntax check on every command before you're asked to run it.
- `-y` to run without confirming. Commands that reach outside the current
  directory always ask, defaulting to no.
- `--think` lets the model reason before answering.
- Promptfoo evals for local and Ollama Cloud models.
- Documentation in `docs/`: a tutorial, how-to guides, reference, explanation
  and architecture decision records.
