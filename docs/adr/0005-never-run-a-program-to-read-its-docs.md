# 5. Never run a program to read its documentation

Date: 2026-10-01

## Status

Accepted

Amends [ADR 0001](0001-read-docs-from-the-installed-system.md)

## Context

ADR 0001 fell back to `<program> --help` when a program had no man page and
the user had named it. That runs the program while the prompt is still being
built, before the user has seen or approved any command, even without `-y`.
Not every program honours `--help`: a personal script named `cleanup` may
ignore the flag and simply run. Limiting it to programs the user named makes
this less likely, not impossible.

Options considered:

- **Keep `--help` for named programs.** It still runs code the user never
  approved.
- **Run `--help` only for programs in system directories** such as `/usr/bin`.
  Most programs without a man page are installed elsewhere, under Homebrew or
  `~/.local/bin`, so the fallback would rarely apply, and system directories
  hold scripts too.
- **Read only man pages.**

## Decision

Read only man pages. Nothing runs before the user confirms a command.

## Consequences

- A program without a man page gets no reference, named or not. The model
  falls back on what it already knows about the program.
- "Nothing runs before you answer the prompt" is now true without exceptions,
  and the safety page can say so.
