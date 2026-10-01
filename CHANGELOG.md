# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- A command that loads a zsh function and then calls it, such as
  `autoload -Uz zmv && zmv …`, is no longer rejected as "command not found".

## [0.2.0] - 2026-10-01

### Added

- `tterm --version` (`-V`) prints the installed version.

### Changed

- Releases on PyPI come with provenance attestations linking each file to the
  GitHub workflow that built it.

### Security

- `THETATERM_BASE_URL` must be an `http` or `https` URL; `file:` and other
  schemes are refused instead of read.

## [0.1.1] - 2026-10-01

### Added

- Published on PyPI: `uv tool install thetaterm`.

### Changed

- README links point at GitHub, so they work on the PyPI project page.

## [0.1.0] - 2026-10-01

### Added

- `tterm`: describe a task, get a shell command for your OS, tool flavour
  (GNU, BSD, BusyBox) and login shell (sh, bash, zsh, ksh, dash; others
  fall back to bash), confirm, run.
- Interactive mode, and one-shot mode with `-q`.
- Any OpenAI-compatible endpoint via `THETATERM_BASE_URL`, with
  `THETATERM_MODEL` and `THETATERM_API_KEY`.
- Settings read from `~/.config/thetaterm/.env`.
- The relevant parts of the installed command's `man` page go into the
  prompt. Nothing runs before you confirm a command.
- A syntax check on every command before you're asked to run it.
- `-y` to run without confirming. Commands that reach outside the current
  directory always ask, defaulting to no: absolute, `~` and `..` paths,
  variables such as `$HOME`, `cd` home or back, and `sudo`.
- `--think` lets the model reason before answering.
- Promptfoo evals for local and Ollama Cloud models.
- Documentation in `docs/`: a tutorial, how-to guides, reference, explanation
  and architecture decision records.

[Unreleased]: https://github.com/thetaplex/thetaterm/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/thetaplex/thetaterm/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/thetaplex/thetaterm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thetaplex/thetaterm/releases/tag/v0.1.0
