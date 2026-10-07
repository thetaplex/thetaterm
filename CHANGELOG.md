# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-10-07

### Changed

- The man pages of the first two installed programs the model suggests go in
  the prompt, not just the first. When the model ranks the wrong program
  first, it can still use the right one: asked for an MD5 checksum,
  `gemma4:e4b-mlx` now writes `md5`, not `shasum -a 1`. Judged by
  `claude-opus-5` on the 50 eval queries, it passed 46, against 43 with one
  program and 45 with three. See ADR 0007.
- The model lists the steps and checks each option exists on this system
  before it writes the command, in a code block. Judged by
  `claude-opus-5`, `gemma4:e4b-mlx` passed 40 of the 46 git eval queries,
  against 36, and 47 of the 50 general ones, against 46. It takes about
  twice as long to answer.
- The prompts mark each part with a tag, such as `<environment>`,
  `<reference>`, `<rules>` and `<task>`, so a man page can't read as
  instructions, and start by saying what the model is for.

### Fixed

- Eval assertions that passed commands that fail on macOS: `du -s` with a
  depth, `date -I date`, macOS `top` with a Linux sort key or piped without
  `-l`, `tar -t` without `-f`, `du -a` for the largest files, and
  `git branch --merged main` piped to `git branch -d` without leaving out
  `main`. They now also pass `gunzip < archive.tar.gz | tar -x`, and
  `sort -nr` after `ls` no longer counts as `ls -r`.
- Eval traces keep up to 20,000 characters of each prompt, not 4,000, so
  `just view` shows the whole of a prompt with two man page excerpts.

## [0.3.0] - 2026-10-04

### Added

- Short notes that ship with thetaterm go before a program's man page excerpt,
  for facts the excerpt tends to miss: `awk` (fields split on spaces, not
  commas), `ps` (`--sort` is GNU only), `curl` (saves nothing without `-O` or
  `-o`), `ping` (runs until stopped without `-c`), `sed` (BSD and GNU `-i`
  differ) and `grep` (`-r` with a file pattern misses subdirectories).
- Evals can be checked by judge models instead of, or as well as, their
  assertions: `just eval local tests judge` or `both`. Assertions can pass a
  command that looks right but uses an option the program doesn't have.
  `configs/judges.yaml` lists the judges, each with its own provider and model
  and enabled or not; every enabled judge checks each answer, in parallel.
- A git eval, `just eval local git`: 46 queries from a regular development
  flow, such as rebasing onto origin, fixup commits, stashing staged changes,
  resolving conflicts, bisecting and safe force pushes. `tests.yaml` keeps
  its sample of 5.
- In interactive mode, a line that starts with `!` runs as a shell command,
  as typed, without the model: `!git status`.

### Changed

- The README asks for a model with at least 3 billion parameters. In the evals,
  `qwen2.5-coder:3b` passed 46 of 50 queries and `qwen2.5-coder:0.5b` 22.
- The model is asked for a single program, and a pipeline or `&&` only when one
  program can't do the task.
- Eval configs and queries are in separate folders, `evals/promptfoo/configs/`
  and `evals/promptfoo/tests/`, so `just eval` can't take one for the other.
  Each model in a config has an `enabled` switch.

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

[Unreleased]: https://github.com/thetaplex/thetaterm/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/thetaplex/thetaterm/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/thetaplex/thetaterm/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/thetaplex/thetaterm/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/thetaplex/thetaterm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thetaplex/thetaterm/releases/tag/v0.1.0
