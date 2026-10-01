# 1. Read documentation from the installed system

Date: 2026-09-30

## Status

Accepted

## Context

Thetaterm is meant to work with small models that run on a laptop. They know
what common tools do, but they don't reliably know which options a tool has on
a particular system. GNU, BSD and BusyBox versions of `find`, `sed`, `date`,
`ps` and others differ, and a command right for one can fail or misbehave on
another.

Options considered:

- **Rely on the model.** This needs a larger model, and even larger models
  default to GNU options.
- **Use `apropos` to pick the tool.** It matches man page summaries by
  substring and offered wrong tools. For example, `ahost` matched "IP addresses
  of this machine".
- **Bundle or fetch documentation.** It wouldn't match the versions actually
  installed.
- **Ask the model to name tools, keep the first one installed, and put its
  local man page in the prompt.**

## Decision

The model suggests up to five programs, and Thetaterm keeps the first one
`which` finds. Thetaterm puts an excerpt of that program's installed `man`
page in the prompt: whole option entries, ranked by rare words from the
request, capped at 3,500 characters. If there's no man page, it uses
`--help`, but only for a program the user named.

## Consequences

- Commands follow the options of the tools actually installed.
- Each request makes two model calls, the man page lookup adds latency, and
  the excerpt takes up context.
- Quality depends on the man page. A tool without one gets no reference unless
  the user names it.
- The 3,500-character cap was tuned on `gemma4:e4b`: 3,000 and 5,000 did worse.
  Other models may want a different size.
- Reasoning models do as well without it, so `--think` skips this step.
